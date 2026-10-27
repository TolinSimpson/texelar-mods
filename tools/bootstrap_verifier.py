"""Acquire a maintainer-pinned engine verifier, never a submission binary."""
import argparse
import hashlib
import io
from pathlib import Path
import re
import zipfile
from catalog import fetch, require


def install(url, sha256, destination):
    require(re.fullmatch(r"https://raw\.githubusercontent\.com/TolinSimpson/[A-Za-z0-9_.-]+/[0-9a-f]{40}/[A-Za-z0-9_./-]+\.zip", url or ""),
            "Configure TRUSTED_VERIFIER_URL to a maintainer-owned, full-commit-pinned ZIP")
    require(re.fullmatch(r"[0-9a-f]{64}", sha256 or ""), "Configure TRUSTED_VERIFIER_SHA256")
    data = fetch(url, 64 * 1024 * 1024)
    require(hashlib.sha256(data).hexdigest() == sha256, "Trusted verifier digest mismatch")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        require(len(entries) == 2 and {e.filename for e in entries} == {"Texelar.exe", "base.texelar"},
                "Verifier ZIP must contain only Texelar.exe and base.texelar")
        require(sum(e.file_size for e in entries) <= 128 * 1024 * 1024, "Verifier expansion ceiling")
        for entry in entries:
            require(0 < entry.file_size <= 64 * 1024 * 1024 and not entry.is_dir()
                    and (entry.external_attr >> 16) & 0o170000 != 0o120000, "Unsafe verifier entry")
            with archive.open(entry) as source:
                content = source.read(entry.file_size + 1)
            require(len(content) == entry.file_size, "Truncated verifier entry")
            (destination / entry.filename).write_bytes(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("sha256")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    install(args.url, args.sha256, args.destination)
