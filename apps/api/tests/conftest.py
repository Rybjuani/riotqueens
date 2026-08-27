"""Legacy domain tests run against the explicit pre-auth compatibility mode.

Authentication regressions switch the setting back on and inject a verifier;
no CI test calls Auth0.
"""

import os

# Force pre-auth defaults for the suite. setdefault would leave a developer
# shell's RIOTQUEENS_AUTH_ENABLED=true in place and break most domain tests.
os.environ["RIOTQUEENS_AUTH_ENABLED"] = "false"
# Prefer in-process stores in unit tests unless a case opts into Postgres.
os.environ.pop("DATABASE_URL", None)
