# Prepare a submission

Submissions are preparation material while this catalog is being built. They
remain unverified until the independent validation and maintainer review gates
are available and complete.

## Prepare the creator repository

Use your own public GitHub repository. Keep the editable source and the exact
exported package together so reviewers can compare them without rebuilding or
bumping the published version. A suggested directory layout is:

```text
assets/                 editable add-on assets
inputs/                 recipes and other reproducible authoring inputs
dist/<id>.texelar       the frozen exported package
manifest/<id>.addon     the matching exported manifest
previews/               representative images
evidence/               frozen reports, provenance and dependency locks
LICENSE                 terms for your content
ATTRIBUTION.md          third-party credits and applicable licenses
README.md               description, limitations and version changes
```

Prepare this directory manually from an accepted workspace export for now; this
repository does not provide a GitHub-ready export command. Preserve the original
export bytes. Do not rerun a version-bumping export to verify an existing version.
Include required attribution and only content you have permission to publish.
Remove credentials, tokens, private files and unrelated workspace history.

For generated content, retain recipes, seed, game, profile, difficulty, dependency
locks, checker/playtest reports and previews. Failed, incomplete or unverified
required checks remain unfinished. Creator reports provide provenance; they
cannot supply the catalog's trusted passing verdict.

## Publish using GitHub's browser

1. Create or open your public creator repository on GitHub.
2. Use **Add file > Upload files** to upload the prepared directory contents,
   preserving their relative paths, then commit. Check that the source, licenses,
   reports and package are visible in the repository.
3. Open that commit and copy its full 40-character commit SHA. A version tag can
   help people discover a release, but a branch, tag or abbreviated SHA is not a
   catalog pin. Keep each package at or below 25 MiB.
4. Fork `TolinSimpson/texelar-mods`. Copy `submissions/TEMPLATE.md` to a uniquely
   named Markdown file under `submissions/` in your fork. Fill in its exact
   repository, commit and paths, then commit the file.
5. Use **Contribute > Open pull request** to submit that file to this repository.
   Explain the change and disclose known limitations. Leave the template itself
   unchanged.

An agent may prepare your directory, commits and submission, and may publish
when you explicitly authorize it using your GitHub access. The game must never
collect the agent's GitHub credentials. This catalog does not require GitHub
Releases or an in-game GitHub login.

## Review and updates

The submission claims an add-on id; it does not reserve or verify ownership.
Maintainers must verify the submitting repository owner before first
registration. Transfers and renames need explicit maintainer review. Reserved
or impersonating names are rejected; `base` is reserved for the engine.

Identity, exact version, compatibility, capabilities, dependencies and package
hash must be independently derived from the checked package. Do not maintain a
second hand-authored manifest in this catalog. Each update needs a new submission
and approval. An existing identity/version/hash is immutable; changing package
bytes requires a new version.

Do not add files under `catalog/` as a creator submission. The native catalog
schema and trusted publication path are pending. Maintainers cannot mark a
version approved until its required checks and ownership review are complete.
