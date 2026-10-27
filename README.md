# Texelar Mods

The public home for Texelar's curated add-on catalog metadata and submission tools.

**Status: tooling implemented; launch configuration pending.** There are no
approved add-ons or published catalog yet. Maintainers must configure the pinned
trusted engine verifier, branch protection and publication review environment.
A submitted issue or pull request does not approve an add-on.

## How the library works

Creators keep editable assets, licenses, previews, evidence and exported
`.texelar` packages in their own public GitHub repositories. This repository
holds reviewed catalog metadata. Each approved version will pin an exact
repository commit, package path, byte count and SHA-256 digest.

Texelar 0.132 adds an in-game Library with a cached native catalog, exact-commit
downloads, digest checks and transactional native installation. Players need no
Git or GitHub account. Fresh downloads require the catalog to be published.

- [Prepare a submission](docs/submissions.md)
- [Maintainer review and publication policy](docs/review-policy.md)
- [Machine-readable submission template](submissions/TEMPLATE.submission)
- [Tools, native schema and launch setup](docs/tooling.md)
- [Catalog status](catalog/README.md)
- [Report a catalog or package problem](https://github.com/TolinSimpson/texelar-mods/issues/new)

## Repository boundaries

This is a metadata catalog. Add-on packages and creator source stay in creator
repositories. Each add-on retains its author's license; catalog inclusion does
not grant redistribution permission or endorse its writing, pacing or enjoyment.

The initial package ceiling is **25 MiB (26,214,400 bytes)**. Package identity,
version, compatibility, capabilities and exact dependencies must come from the
independently checked package. Hosting and review metadata belong here. A new
upstream tag or commit never approves a new version automatically.

The workflows validate submissions as data in disposable read-only jobs and
publish reviewed records in a separate gated job. They never execute creator
workflows or scripts. Local tooling tests use Python's standard library:

```powershell
python -m unittest discover -s tests -v
```

See the launch checklist before enabling publication. The private engine source,
build artifacts and game assets are not included in this repository.
