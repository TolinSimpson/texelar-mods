# Maintainer review and publication policy

This policy describes the launch requirements. The bootstrap has no validator,
ownership registry, published catalog or publication automation.

## Validate every submitted version

- Treat all repository content and submitted reports as untrusted data. Validate
  exact owner/repository/full commit/path inputs before fetching. Reject unsafe
  paths, unexpected origins, alternate schemes and redirects outside the allowed
  GitHub content hosts. Bound transfer sizes, redirects, time and decoded images.
- Fetch into a disposable restricted environment. Use trusted engine tools from
  a maintainer-controlled revision. Do not execute submitted workflows, scripts
  or pull-request code. Validation jobs have read-only access and no secrets or
  publication credentials; do not add `pull_request_target` execution of PR code.
- Enforce the 25 MiB package ceiling and recompute size and SHA-256. Independently
  inspect package structure, manifest, content and exact dependencies. Verify
  source/export equivalence without mutating source or invoking a version-bumping
  export. Run the applicable native checks and runtime harnesses with pinned
  inputs; retain reports and limitations.
- Reject duplicate or conflicting versions, unavailable exact dependencies,
  unsupported required capabilities, source/export mismatch and any required
  failed, incomplete or unverified check. Creator-supplied reports cannot grant
  approval.
- Verify repository ownership before reserving a new id. Protect engine-owned
  and impersonating names. Review transfers and repository renames explicitly.

## Approve and publish

A maintainer reviews the independently produced evidence and each specific
version record before approval. Author reputation, a merged submission or a tag
does not approve this or any future version. Human catalog approval is separate
from judging content enjoyable.

Catalog records use Texelar's native line-based document family. Derive logical
identity, compatibility, capabilities and dependencies from checked packages.
Record hosting, ownership, tags, review and evidence status separately. Each
approved package pins a full commit, paths, byte count and SHA-256. Changing bytes
requires a new version; changing a hosting location must preserve the approved
identity/version/hash and receive review.

Publish one bounded downloadable catalog only from protected reviewed state.
Protect the publication branch/environment and require the owning validation
checks before enabling publication. Never run a submission-supplied publishing
command. Validation and credentialed publication must remain separate.

## Problems and blocked versions

Use this repository's issues to report broken downloads, ownership disputes,
impersonation, harmful content or incorrect metadata. Include the add-on id,
version, pinned commit and relevant public evidence. Never post secrets or
private creator files.

Keep reviewed tombstones and blocked-version records in the published catalog
with reporting links. Apply refreshed block records before activation. Preserve
unrelated installed versions and creator work. An offline client cannot promise
immediate revocation and must display catalog freshness. Deleted upstream
packages become unavailable for fresh download; existing local copies and exact
dependency locks remain usable subject to the applicable block policy.

## Launch acceptance

Before calling the library live, complete deterministic catalog/network fixture
tests, ownership/version/dependency checks, adversarial submission checks and
secret-free CI verification. Exercise export, creator commit, reviewed catalog
and install in a disposable integration repository. Do not publish test add-ons
as approved catalog entries. Complete the engine's required package, authoring,
UI, packed and stripped-build gates and the separate human review.
