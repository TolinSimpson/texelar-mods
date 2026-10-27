# Texelar Mods

The public home for Texelar's planned curated add-on catalog.

**Status: repository bootstrap.** There are no approved add-ons or downloadable
catalog yet. Submission validation, protected catalog publication and the
in-game Library are not configured. A submitted issue or pull request does not
make an add-on approved or installable.

## How the library will work

Creators keep editable assets, licenses, previews, evidence and exported
`.texelar` packages in their own public GitHub repositories. This repository
holds reviewed catalog metadata. Each approved version will pin an exact
repository commit, package path, byte count and SHA-256 digest.

Players will browse a cached catalog and install from inside Texelar without
Git or a GitHub account. That engine integration is still pending.

- [Prepare a submission](docs/submissions.md)
- [Maintainer review and publication policy](docs/review-policy.md)
- [Submission template](submissions/TEMPLATE.md)
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

Before launch, maintainers must connect trusted engine verification, ownership
checks, the native line-based catalog format, blocked-version records, protected
publication and the in-game client. No publication workflow is installed by this
bootstrap.
