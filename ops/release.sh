#!/usr/bin/env bash
# RiotQueens release — git archive + SHA-256 manifest + atomic current switch.
# Owner 2026-08-28: deploy strategy B (LEY 0).
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-ubuntu@148.113.167.121}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/luxriot_vps}"
REMOTE_ROOT="${REMOTE_ROOT:-/opt/riotqueens}"
REF="${1:-HEAD}"

SSH=(ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o BatchMode=yes "$REMOTE_HOST")
SCP=(scp -i "$SSH_KEY" -o IdentitiesOnly=yes -o BatchMode=yes)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --verify "$REF" >/dev/null 2>&1; then
  echo "Error: unknown ref $REF"
  exit 1
fi

COMMIT="$(git rev-parse "$REF")"
SHORT="$(git rev-parse --short=12 "$REF")"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
RELEASE_NAME="archive-${STAMP}-${SHORT}"
RELEASE_DIR="${REMOTE_ROOT}/releases/${RELEASE_NAME}"

echo "Releasing $COMMIT as $RELEASE_NAME → $REMOTE_HOST:$RELEASE_DIR"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

ARCHIVE="$TMP/${RELEASE_NAME}.tar"
MANIFEST="$TMP/MANIFEST.sha256"
META="$TMP/RELEASE.json"

git archive --format=tar --prefix="${RELEASE_NAME}/" "$COMMIT" > "$ARCHIVE"
# Manifest over archive members (deterministic paths inside tar prefix).
tar -tf "$ARCHIVE" | sort > "$TMP/paths.txt"
# Hash file contents by extracting to a staging dir.
STAGE="$TMP/stage"
mkdir -p "$STAGE"
tar -xf "$ARCHIVE" -C "$STAGE"
(
  cd "$STAGE/$RELEASE_NAME"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$MANIFEST"

python3 - "$COMMIT" "$RELEASE_NAME" "$MANIFEST" "$META" <<'PY'
import hashlib, json, sys, pathlib
commit, name, manifest_path, meta_path = sys.argv[1:5]
manifest_text = pathlib.Path(manifest_path).read_text(encoding="utf-8")
meta = {
    "commit": commit,
    "release_name": name,
    "created_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    "manifest_sha256": hashlib.sha256(manifest_text.encode()).hexdigest(),
    "file_count": sum(1 for line in manifest_text.splitlines() if line.strip()),
}
pathlib.Path(meta_path).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
print(json.dumps(meta, indent=2))
PY

# Prefer GitHub codeload on the VPS (same commit tree; avoids slow home→VPS uplink).
# Local MANIFEST/META remain the source of truth for the release record uploaded after extract.
"${SSH[@]}" "sudo mkdir -p '${REMOTE_ROOT}/releases' '${REMOTE_ROOT}/shared' && sudo chown -R ubuntu:ubuntu '${REMOTE_ROOT}/releases' '${REMOTE_ROOT}/shared' || true"

"${SCP[@]}" "$MANIFEST" "${REMOTE_HOST}:/tmp/${RELEASE_NAME}.MANIFEST.sha256"
"${SCP[@]}" "$META" "${REMOTE_HOST}:/tmp/${RELEASE_NAME}.RELEASE.json"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
RELEASE_DIR='${RELEASE_DIR}'
RELEASE_NAME='${RELEASE_NAME}'
REMOTE_ROOT='${REMOTE_ROOT}'
COMMIT='${COMMIT}'
rm -rf "\$RELEASE_DIR"
mkdir -p "\$RELEASE_DIR"
TMP=\$(mktemp -d)
cd "\$TMP"
curl -fsSL -o repo.tgz "https://codeload.github.com/Rybjuani/riotqueens/tar.gz/\${COMMIT}"
tar -xzf repo.tgz
SRC=\$(find . -maxdepth 1 -type d -name 'riotqueens-*' | head -1)
test -n "\$SRC"
shopt -s dotglob
mv "\$SRC"/* "\$RELEASE_DIR"/
shopt -u dotglob
cp "/tmp/\${RELEASE_NAME}.MANIFEST.sha256" "\$RELEASE_DIR/MANIFEST.sha256"
cp "/tmp/\${RELEASE_NAME}.RELEASE.json" "\$RELEASE_DIR/RELEASE.json"
# Refresh on-disk manifest from extracted tree (authoritative for this host)
(
  cd "\$RELEASE_DIR"
  find . -type f ! -name MANIFEST.sha256 ! -name RELEASE.json -print0 | sort -z | xargs -0 sha256sum
) > "\$RELEASE_DIR/MANIFEST.sha256"
if [[ -f "\${REMOTE_ROOT}/shared/runtime.env" ]]; then
  ln -sfn "\${REMOTE_ROOT}/shared/runtime.env" "\$RELEASE_DIR/runtime.env"
  ln -sfn "\${REMOTE_ROOT}/shared/runtime.env" "\$RELEASE_DIR/.env"
fi
sudo ln -sfn "\$RELEASE_DIR" "\${REMOTE_ROOT}/current.new"
sudo mv -Tf "\${REMOTE_ROOT}/current.new" "\${REMOTE_ROOT}/current"
sudo chown -h ubuntu:ubuntu "\${REMOTE_ROOT}/current" || true
echo "current -> \$(readlink -f \${REMOTE_ROOT}/current)"
cd "\${REMOTE_ROOT}/current"
chmod +x ops/deploy.sh ops/release.sh 2>/dev/null || true
test -f DOSSIER_MAESTRO.md
./ops/deploy.sh
echo "Release active: \$RELEASE_NAME"
cat RELEASE.json
EOF

echo "Release complete: $RELEASE_NAME ($COMMIT)"
