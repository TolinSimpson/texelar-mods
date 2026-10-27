# Tools and launch setup

Python 3.13 and a trusted Texelar 0.132+ Windows build are required for native
verification. Python has no third-party dependencies. `Texelar.exe` and its
trusted `base.texelar` must come from the maintainer's own engine build.

## Creator export

Run from this repository, using paths to your frozen accepted export:

```powershell
python tools/catalog.py export --engine C:/Texelar/Texelar.exe --package C:/export/mod.texelar --source C:/export/assets --manifest C:/export/mod.addon --license C:/export/LICENSE --attribution C:/export/ATTRIBUTION.md --preview C:/export/preview.jpg --evidence C:/export/evidence --output C:/export/github-ready
```

Optional `--inputs` preserves native recipes, themes, intents, kits and scopes.
The destination must be new. Source payloads and external manifest must match
the package byte-for-byte. Only selected assets, the frozen package, explicit
license/attribution, bounded JPEG and frozen evidence are copied. Secret-pattern
checks supplement the creator's review; they do not establish absence of secrets.
No publishing, login or version bump occurs. Follow the generated `SUBMIT.md`.

## Validation and records

`check-submission` checks framing; `verify` fetches only exact committed source
data and invokes the trusted native verifier. Repository blobs are checked
against their Git object hashes. Symlinks, submodules, executable blobs, redirects,
unsafe paths, oversized trees and likely credentials are refused. Registry jobs
run independent native preflight, source comparison and applicable content/UI
runtime jobs. Creator reports never substitute for those results.

```powershell
python tools/catalog.py verify submissions/example/1.0.0.submission --engine C:/Texelar/Texelar.exe --base C:/Texelar/base.texelar --work work
```

The resulting `texelar-addon-catalog 1` record is **pending**. Maintain ownership
proof in `owners/<id>.owner` (see that directory's README). Only a reviewed
`approved`, `blocked` or `withdrawn` version record belongs under `records/`.
Each entry contains repository, full commit, manifest/package paths, size/SHA-256,
review status, tags, evidence limitations, changes and report URL. Optional
`preview <path> <bytes> <sha256>` pins a JPEG of at most 256 KiB and 1024x1024.
`meta` lines contain the checked native manifest verbatim; do not hand-author a
conflicting identity or dependency schema. Entries end with `end`.

Publication re-verifies every new approved version. Previously published bytes
and manifest metadata are immutable. History and block/withdrawal tombstones
must remain present even when the creator deletes the upstream repository.
Changed hosting locations do not change package identity. Deleted packages cannot
be freshly downloaded; exact installed local copies remain usable offline unless
the current cached policy blocks activation.

## Launch checklist (not configured by these tools)

1. Build and review a distributable trusted engine verifier. Decide which engine
   binaries and base assets may be publicly distributed; this repository does
   not grant that permission. Host a ZIP with only `Texelar.exe` and
   `base.texelar` at a full-commit raw GitHub URL. Set repository variables
   `TRUSTED_VERIFIER_URL` and `TRUSTED_VERIFIER_SHA256` to that URL and ZIP digest.
2. Protect `main` and the `catalog` output branch. Require independent review of
   policy, ownership and every version record. Restrict output-branch writes to
   maintainers and the reviewed publication workflow. Workflow code changes
   require policy review; never merge submission-supplied commands into publishing.
3. Create the `catalog-publication` environment with required human reviewers.
   `publish.yml` refuses publication if main is unprotected or the environment
   has no required-reviewer rule. Validation jobs have read-only tokens and no
   publication secrets. The separate publication job writes data only after
   protected source checks and environment approval.
4. Exercise export, creator commit, read-only PR validation, ownership/version
   review, publication and in-game installation in a disposable integration
   repository. Do not use public production submissions as incidental tests.
5. Dispatch **Publish reviewed catalog**, enabling `initial_catalog` only for
   the first output branch. Thereafter previous history must be available and
   valid; fetch failures must never reset it. The client reads
   `https://raw.githubusercontent.com/TolinSimpson/texelar-mods/catalog/catalog/library.catalog`.

The native client uses system HTTPS certificate checks, deadlines, cancellation,
bounded data and exact commit pins. It never embeds a GitHub credential. Offline
freshness is displayed; immediate revocation cannot be promised offline. Human
catalog approval and human content/readability review are separate judgments.
