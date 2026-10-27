"""Read previous publication; only an explicit first publication accepts 404."""
import argparse
from pathlib import Path
import urllib.error
from catalog import api, commit, fetch, parse_catalog, repository, require


def previous(repo, output, initial=False):
    repository(repo)
    try:
        branch = api(f"repos/{repo}/branches/catalog")
    except urllib.error.HTTPError as error:
        require(error.code == 404 and initial, "Previous publication unavailable; refusing to discard history")
        return False
    sha = commit(branch["commit"]["sha"])
    Path(output).write_bytes(fetch(f"https://raw.githubusercontent.com/{repo}/{sha}/catalog/library.catalog", 8388608))
    parse_catalog(output)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository")
    parser.add_argument("output", type=Path)
    parser.add_argument("--initial", action="store_true")
    args = parser.parse_args()
    previous(args.repository, args.output, args.initial)
