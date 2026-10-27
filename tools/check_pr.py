"""Trusted base-branch runner; download only PR submission documents as data."""
import argparse
from pathlib import Path
import re
from catalog import api, commit, fetch, identity, parse_catalog, repository, require, verify


def check(repo, number, root, work, engine, base):
    repository(repo)
    require(number > 0, "Invalid PR number")
    pr = api(f"repos/{repo}/pulls/{number}")
    head_repo = repository(pr["head"]["repo"]["full_name"])
    head_sha = commit(pr["head"]["sha"])
    changed = []
    for page in range(1, 11):
        files = api(f"repos/{repo}/pulls/{number}/files?per_page=100&page={page}")
        require(isinstance(files, list), "Malformed PR file list")
        changed.extend(files)
        if len(files) < 100:
            break
    else:
        raise ValueError("PR file ceiling exceeded")
    require(len(changed) == pr["changed_files"], "Truncated PR file list")
    submissions = []
    for item in changed:
        name = item["filename"]
        require(re.fullmatch(r"submissions/[a-z0-9_-]{1,31}/[0-9]+\.[0-9]+\.[0-9]+\.submission", name),
                "Catalog/code/policy changes require separate maintainer review; PR code is never executed")
        require(item["status"] in {"added", "modified"}, "Submission deletion/rename requires maintainer review")
        destination = Path(work) / "requests" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(fetch(f"https://raw.githubusercontent.com/{head_repo}/{head_sha}/{name}", 65536))
        submissions.append((name, destination))
    for index, (name, path) in enumerate(submissions):
        result = verify(path, root, Path(work) / f"check-{index}", engine, base)
        _, records = parse_catalog(result)
        addon, version = identity(records[0])
        require(name == f"submissions/{addon}/{version}.submission", "Submitted path differs from checked package identity")
    require(submissions, "No version submissions found")
    print("Independent checks retained; ownership and per-version maintainer approval remain required.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repository")
    p.add_argument("number", type=int)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--engine", type=Path, required=True)
    p.add_argument("--base", type=Path, required=True)
    args = p.parse_args()
    check(args.repository, args.number, args.root, args.work, args.engine, args.base)
