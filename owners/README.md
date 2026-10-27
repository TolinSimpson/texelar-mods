# Verified id ownership

Only maintainers add `owners/<id>.owner`, after verifying repository ownership.
Native fields are `repository`, `repository-id`, `owner-id`, `verified-commit`
and `evidence`, after header `texelar-addon-owner 1`. GitHub's numeric repository
and owner ids must match current API data. The proof commit must be on the
owner's default branch; merely fetching an unmerged fork commit is insufficient.
Link the maintainer's ownership review in `evidence`.

Reserved ids include `base`, `texelar`, `official` and `engine`. Repository moves,
renames and ownership transfers require a fresh explicit maintainer review.
An ownership record never approves content or future versions.
