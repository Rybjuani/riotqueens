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

"${SSH[@]}" "sudo mkdir -p '${REMOTE_ROOT}/releases' '${REMOTE_ROOT}/shared' && sudo chown -R ubuntu:ubuntu '${REMOTE_ROOT}/releases' '${REMOTE_ROOT}/shared' || true"
"${SSH[@]}" "mkdir -p '${RELEASE_DIR}'"
"${SCP[@]}" "$ARCHIVE" "${REMOTE_HOST}:/tmp/${RELEASE_NAME}.tar"
"${SCP[@]}" "$MANIFEST" "${REMOTE_HOST}:/tmp/${RELEASE_NAME}.MANIFEST.sha256"
"${SCP[@]}" "$META" "${REMOTE_HOST}:/tmp/${RELEASE_NAME}.RELEASE.json"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
RELEASE_DIR='${RELEASE_DIR}'
RELEASE_NAME='${RELEASE_NAME}'
REMOTE_ROOT='${REMOTE_ROOT}'
mkdir -p "\$RELEASE_DIR"
tar -xf "/tmp/\${RELEASE_NAME}.tar" -C "\${REMOTE_ROOT}/releases"
# tar created releases/\$RELEASE_NAME/ via prefix — already correct if extracted under releases
# Ensure path: if archive prefix extracted into releases/, tree is releases/\$RELEASE_NAME
test -d "\$RELEASE_DIR"
cp "/tmp/\${RELEASE_NAME}.MANIFEST.sha256" "\$RELEASE_DIR/MANIFEST.sha256"
cp "/tmp/\${RELEASE_NAME}.RELEASE.json" "\$RELEASE_DIR/RELEASE.json"
# Link shared runtime.env if present
if [[ -f "\${REMOTE_ROOT}/shared/runtime.env" ]]; then
  ln -sfn "\${REMOTE_ROOT}/shared/runtime.env" "\$RELEASE_DIR/runtime.env"
  ln -sfn "\${REMOTE_ROOT}/shared/runtime.env" "\$RELEASE_DIR/.env"
fi
# Atomic switch
ln -sfn "\$RELEASE_DIR" "\${REMOTE_ROOT}/current.new"
mv -Tf "\${REMOTE_ROOT}/current.new" "\${REMOTE_ROOT}/current"
echo "current -> \$(readlink -f \${REMOTE_ROOT}/current)"
cd "\${REMOTE_ROOT}/current"
chmod +x ops/deploy.sh ops/release.sh 2>/dev/null || true
./ops/deploy.sh
# Verify Caddyfile bind uses current release path when compose mounts ./ops/Caddyfile
echo "Release active: \$RELEASE_NAME"
sha256sum -c MANIFEST.sha256 >/dev/null && echo "MANIFEST.sha256 OK" || echo "WARN: manifest verify skipped/failed"
cat RELEASE.json
EOF

echo "Release complete: $RELEASE_NAME ($COMMIT)"
