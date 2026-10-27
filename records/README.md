# Reviewed immutable versions

Store one native `texelar-addon-catalog 1` record at
`records/<checked-id>/<checked-version>.catalog`. Generate it with the trusted
native verifier; do not hand-author a second package manifest. The verifier emits
`review pending`. Only a maintainer may change that to `approved` after checking
the independent reports and verified ownership record for this specific version.

Retain blocked/withdrawn records as tombstones. Never replace an existing
identity/version's bytes, hash or manifest. `tools/catalog.py build` recomputes
new approved records through the trusted verifier and builds the bounded catalog.
Previously published unchanged bytes retain their reviewed evidence if upstream
disappears; new installs then fail explicitly. Hosting changes receive fresh checks.
