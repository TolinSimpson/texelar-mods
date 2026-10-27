# Catalog

No versions are approved and no runtime catalog is published yet.

Reviewed records live in `records/` on main. The gated publication workflow writes
the bounded native `catalog/library.catalog` on the separate `catalog` branch.
Configure the trusted verifier and protection settings before first publication;
see [launch setup](../docs/tooling.md). Do not invent placeholder approvals or
an empty document that a client could mistake for a working catalog.

Creator submissions belong in `submissions/`. Packages remain at commit-pinned
paths in creator repositories. The launch catalog must also represent reviewed
tombstones, blocked versions, evidence limitations and reporting links.
