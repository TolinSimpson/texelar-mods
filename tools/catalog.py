"""Trusted catalog tooling. Submissions and creator trees are data, never code.

Native package/UI parsing stays in the pinned Texelar verifier. This tool owns
GitHub fetching, ownership records and protected-state catalog assembly only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

CATALOG_LIMIT = 8 * 1024 * 1024
PACKAGE_LIMIT = 25 * 1024 * 1024
FETCH_LIMIT = 128 * 1024 * 1024
FIELDS = {"repository", "commit", "source", "inputs", "manifest", "package", "license",
          "attribution", "preview", "evidence", "tags", "changes", "report", "profile"}
SECRET = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
                    rb"AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative(value):
    require(isinstance(value, str) and 0 < len(value) < 256
            and re.fullmatch(r"[A-Za-z0-9_./-]+", value), "Unsafe relative path")
    parts = value.split("/")
    for part in parts:
        require(part and not part.startswith(".") and not part.endswith((".", " "))
                and len(part) < 96, "Unsafe path segment")
        require(part.split(".")[0].upper() not in
                {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)),
                 *(f"LPT{i}" for i in range(10))}, "Reserved device name")
    return value


def repository(value):
    require(isinstance(value, str) and re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}", value)
        and not value.endswith("."), "Invalid owner/repository")
    return value


def commit(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value),
            "A full immutable commit SHA is required")
    return value


def document(path, header, allowed, optional=()):
    data = Path(path).read_bytes()
    require(0 < len(data) <= 65536 and data.endswith(b"\n") and not SECRET.search(data),
            "Incomplete, oversized or secret-bearing document")
    text = data.decode("utf-8")
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    require(lines and lines.pop(0) == header, "Unsupported native document header")
    result = {}
    for line in lines:
        require(len(line) < 1024 and all(ord(c) >= 32 for c in line), "Invalid physical line")
        key, separator, value = line.partition(" ")
        require(separator and key in allowed and key not in result and value.strip(),
                f"Unknown, duplicate or empty field: {key}")
        result[key] = value
    require(set(allowed) - set(optional) <= set(result), "Missing native document fields")
    return result


def submission(path):
    result = document(path, "texelar-addon-submission 1", FIELDS, {"inputs"})
    repository(result["repository"])
    commit(result["commit"])
    for field in ("source", "manifest", "package", "license", "attribution", "preview", "evidence"):
        relative(result[field])
    if "inputs" in result:
        relative(result["inputs"])
    require(result["package"].endswith(".texelar") and result["manifest"].endswith(".addon"),
            "Incorrect package/manifest extension")
    require(re.fullmatch(r"[a-z0-9_-]{1,31}", result["profile"]), "Invalid profile")
    require(result["report"].startswith(f'https://github.com/{result["repository"]}/issues'),
            "Reporting link must identify the submitted repository's issues")
    require(len(result["tags"]) < 160 and len(result["changes"]) < 256, "Oversized catalog prose")
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused; review the exact repository/content location")


def fetch(url, limit):
    require(url.startswith(("https://api.github.com/", "https://raw.githubusercontent.com/")),
            "Unexpected fetch origin")
    request = urllib.request.Request(url, headers={"User-Agent": "Texelar-Catalog/1"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=10) as response:
        data = response.read(limit + 1)
        require(len(data) <= limit, "Response exceeds its byte ceiling")
        length = response.headers.get("Content-Length")
        require(length is None or int(length) == len(data), "Partial transfer")
        require(not SECRET.search(data), "Possible secret in export; remove it before publishing")
        return data


def api(path):
    return json.loads(fetch("https://api.github.com/" + path, CATALOG_LIMIT))


def run_native(engine, args, report=None):
    engine = Path(engine).resolve(strict=True)
    # An argument vector, no shell and no submission-supplied command. The
    # environment is inherited only from this disposable, secret-free CI job.
    process = subprocess.run([str(engine), *map(str, args)], check=False, timeout=600,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    require(process.returncode == 0, f"Native verification failed: {process.stdout[-2000:]!r}")
    if report:
        verdict = Path(report).read_text(encoding="utf-8")
        require(re.search(r"^summary passed errors 0 warnings \d+ unverified 0 checks [1-9]\d*$",
                          verdict, re.M), "Native verdict is missing or required-unverified")


def fetch_source(spec, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    tree = api(f'repos/{spec["repository"]}/git/trees/{spec["commit"]}?recursive=1')
    require(tree.get("truncated") is False and isinstance(tree.get("tree"), list),
            "GitHub returned a truncated or malformed tree")
    roots = [spec["source"], spec["evidence"]]
    if spec.get("inputs"):
        roots.append(spec["inputs"])
    exact = {spec[k] for k in ("package", "manifest", "license", "attribution", "preview")}
    found, total, deadline = set(), 0, time.monotonic() + 300
    for item in tree["tree"]:
        name = item.get("path", "")
        if name not in exact and not any(name.startswith(root + "/") for root in roots):
            continue
        relative(name)
        require(time.monotonic() < deadline, "Source fetch deadline exceeded")
        if item.get("type") == "tree":
            continue
        require(item.get("type") == "blob" and item.get("mode") == "100644",
                "Symlinks, executable files and submodules are excluded from exports")
        size = item.get("size")
        ceiling = PACKAGE_LIMIT if name == spec["package"] else 262144 if name == spec["preview"] else CATALOG_LIMIT
        require(type(size) is int and 0 < size <= ceiling and len(found) < 4096
                and total + size <= FETCH_LIMIT, "Source tree exceeds bounded file/byte limits")
        require(not any(p.lower() in {".env", "credentials", "secrets"}
                        for p in PurePosixPath(name).parts), "Forbidden export file")
        data = fetch(f'https://raw.githubusercontent.com/{spec["repository"]}/{spec["commit"]}/{name}', size)
        require(len(data) == size and hashlib.sha1(f"blob {size}\0".encode() + data).hexdigest() == item.get("sha"),
                "Commit tree/blob identity or size mismatch")
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        found.add(name)
        total += size
    require(exact <= found and any(p.startswith(spec["evidence"] + "/") for p in found),
            "Missing package, frozen manifest, license, attribution, preview or evidence")
    return output


def parse_catalog(path):
    data = Path(path).read_bytes()
    require(0 < len(data) <= CATALOG_LIMIT and data.endswith(b"\n") and not SECRET.search(data),
            "Malformed or secret-bearing catalog")
    lines = [s for s in data.decode("utf-8").splitlines() if s and not s.startswith("#")]
    require(len(lines) >= 2 and lines[0] == "texelar-addon-catalog 1"
            and re.fullmatch(r"serial [1-9][0-9]{0,19}", lines[1]), "Invalid catalog framing")
    records, current = [], None
    fields = {"repository", "commit", "manifest", "package", "bytes", "sha256", "review",
              "tags", "evidence", "changes", "report"}
    for line in lines[2:]:
        require(len(line) < 1024 and all(ord(c) >= 32 for c in line), "Invalid catalog physical line")
        if line == "entry":
            require(current is None and len(records) < 256, "Nested or excessive catalog records")
            current = {"meta": []}
        elif line == "end":
            require(current is not None and set(current) - {"preview"} == fields | {"meta"}, "Incomplete record")
            repository(current["repository"])
            commit(current["commit"])
            relative(current["manifest"])
            relative(current["package"])
            require(re.fullmatch(r"[0-9a-f]{64}", current["sha256"])
                    and re.fullmatch(r"[1-9][0-9]*", current["bytes"])
                    and int(current["bytes"]) <= PACKAGE_LIMIT, "Invalid package digest/size")
            require(current["review"] in {"pending", "approved", "blocked", "withdrawn"}, "Unknown review state")
            identity(current)
            records.append(current)
            current = None
        else:
            key, separator, value = line.partition(" ")
            require(current is not None and separator and value, "Unexpected catalog record")
            if key == "meta":
                current["meta"].append(value)
            else:
                require(key in fields | {"preview"} and key not in current, "Unknown or duplicate hosting field")
                current[key] = value
    require(current is None, "Truncated catalog record")
    require(len({identity(r) for r in records}) == len(records), "Duplicate immutable id/version")
    return int(lines[1].split()[1]), records


def identity(record):
    fields = {}
    for line in record["meta"]:
        key, _, value = line.partition(" ")
        if key in {"id", "version", "game", "api"}:
            require(key not in fields, "Duplicate manifest identity field")
            fields[key] = value
    require(set(fields) == {"id", "version", "game", "api"}
            and re.fullmatch(r"[a-z0-9_-]{1,31}", fields["id"])
            and fields["id"] not in {"base", "texelar", "official", "engine"}
            and re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", fields["version"]),
            "Invalid or reserved manifest identity")
    return fields["id"], fields["version"]


def write_catalog(records, path, serial):
    require(len(records) <= 256 and 0 < serial <= (1 << 64) - 1, "Catalog bound exceeded")
    fields = ("repository", "commit", "manifest", "package", "bytes", "sha256", "review",
              "tags", "evidence", "changes", "report")
    lines = ["texelar-addon-catalog 1", f"serial {serial}"]
    for record in records:
        lines.append("entry")
        lines.extend(f"{key} {record[key]}" for key in fields)
        if record.get("preview"):
            lines.append("preview " + record["preview"])
        lines.extend("meta " + value for value in record["meta"])
        lines.append("end")
    data = ("\n".join(lines) + "\n").encode("utf-8")
    require(len(data) <= CATALOG_LIMIT, "Catalog exceeds download ceiling")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)


def ownership(record, root):
    addon, _ = identity(record)
    owner = document(Path(root) / "owners" / f"{addon}.owner", "texelar-addon-owner 1",
                     {"repository", "repository-id", "owner-id", "verified-commit", "evidence"})
    require(owner["repository"].lower() == record["repository"].lower(),
            "Id ownership changed; explicit maintainer transfer/rename review required")
    info = api(f'repos/{repository(owner["repository"])}')
    require(str(info["id"]) == owner["repository-id"]
            and str(info["owner"]["id"]) == owner["owner-id"], "Verified repository/owner identity changed")
    verified = commit(owner["verified-commit"])
    # A commit merely reachable through a fork network cannot prove repository
    # ownership. Require the reviewed proof commit on the owner's default branch.
    from urllib.parse import quote
    branch = api(f'repos/{owner["repository"]}/branches/{quote(info["default_branch"], safe="")}')
    comparison = api(f'repos/{owner["repository"]}/compare/{verified}...{commit(branch["commit"]["sha"])}')
    require(comparison["status"] in {"ahead", "identical"}, "Ownership proof is not on the owner's default branch")
    require(owner["evidence"].startswith("https://github.com/"), "Missing human ownership-review evidence")


def dependencies(manifest, root, output):
    selected, pending, total = {}, [], 0
    for line in Path(manifest).read_text(encoding="utf-8").splitlines():
        if line.startswith("requires "):
            parts = line.split()
            require(len(parts) == 3, "Malformed exact dependency")
            pending.append((parts[1], parts[2]))
    while pending:
        addon, version = pending.pop()
        require(re.fullmatch(r"[a-z0-9_-]{1,31}", addon)
                and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version), "Invalid dependency identity")
        if (addon, version) in selected:
            continue
        require(len(selected) < 14, "Dependency closure exceeds native mount budget")
        _, records = parse_catalog(Path(root) / "records" / addon / f"{version}.catalog")
        require(len(records) == 1 and identity(records[0]) == (addon, version)
                and records[0]["review"] == "approved", "Required exact dependency is not approved")
        record = records[0]
        data = fetch(f'https://raw.githubusercontent.com/{record["repository"]}/{record["commit"]}/{record["package"]}',
                     int(record["bytes"]))
        total += len(data)
        require(total <= FETCH_LIMIT and len(data) == int(record["bytes"])
                and hashlib.sha256(data).hexdigest() == record["sha256"], "Dependency digest/size mismatch")
        path = Path(output) / f"{addon}-{version}.texelar"
        path.write_bytes(data)
        selected[(addon, version)] = path
        for line in record["meta"]:
            if line.startswith("requires "):
                parts = line.split()
                require(len(parts) == 3, "Malformed catalog dependency")
                pending.append((parts[1], parts[2]))
    return list(selected.values())


def verify(spec_path, root, work, engine, base):
    spec = submission(spec_path)
    work = Path(work)
    work.mkdir(parents=True, exist_ok=False)
    source = fetch_source(spec, work / "creator")
    evidence = work / "independent-evidence"
    evidence.mkdir()
    result = work / "pending.catalog"
    report = work / "verification.report"
    args = ["--addon-registry-check", source / spec["package"], "--source-assets", source / spec["source"],
            "--source-manifest", source / spec["manifest"], "--base-pack", base, "--output", result,
            "--repository", spec["repository"], "--commit", spec["commit"], "--manifest-path", spec["manifest"],
            "--package-path", spec["package"], "--tags", spec["tags"], "--changes", spec["changes"],
            "--report-link", spec["report"], "--profile", spec["profile"],
            "--preview-path", spec["preview"], "--preview-file", source / spec["preview"],
            "--evidence", "Independent native/runtime checks; human review remains separate.",
            "--evidence-output", evidence, "--content-report", report]
    for path in dependencies(source / spec["manifest"], root, work):
        args += ["--dependency", path]
    run_native(engine, args, report)
    _, records = parse_catalog(result)
    require(len(records) == 1 and records[0]["review"] == "pending", "Verifier must never grant catalog approval")
    return result


def build(root, output, engine, base, work, previous=None):
    root, work = Path(root), Path(work)
    work.mkdir(parents=True, exist_ok=False)
    serial, old = parse_catalog(previous) if previous else (0, [])
    prior = {identity(record): record for record in old}
    records = []
    for path in sorted((root / "records").glob("*/*.catalog")):
        _, entries = parse_catalog(path)
        require(len(entries) == 1, "One immutable version per reviewed record file")
        record = entries[0]
        addon, version = identity(record)
        require(path.relative_to(root).as_posix() == f"records/{addon}/{version}.catalog",
                "Record path does not match checked identity")
        require(record["review"] != "pending", "Pending versions cannot be published")
        ownership(record, root)
        existing = prior.get((addon, version))
        if existing:
            require((record["sha256"], record["bytes"], record["meta"]) ==
                    (existing["sha256"], existing["bytes"], existing["meta"]), "Immutable version bytes/manifest changed")
        unchanged = existing and all(record.get(k) == existing.get(k) for k in
                    ("repository", "commit", "manifest", "package", "sha256", "bytes", "meta", "preview"))
        if record["review"] == "approved" and not unchanged:
            candidate = verify(root / "submissions" / addon / f"{version}.submission", root,
                               work / f"{addon}-{version}", engine, base)
            _, checked = parse_catalog(candidate)
            require(all(record[k] == checked[0][k] for k in record if k != "review"),
                    "Reviewed record differs from independent verifier output")
        records.append(record)
    require(set(prior) <= {identity(record) for record in records}, "Published versions need retained tombstones")
    write_catalog(records, output, max(serial + 1, int(time.time())))
    run_native(engine, ["--addon-catalog-check", output, "--content-report", work / "catalog.report"],
               work / "catalog.report")
    return output


def local_bytes(path, limit, digest=None):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        require(not parent.is_symlink() and not getattr(parent, "is_junction", lambda: False)(),
                "Local exports cannot traverse links or junctions")
    info = path.stat()
    require(path.is_file() and info.st_nlink == 1 and 0 < info.st_size <= limit,
            "Unsafe, empty or oversized local export input")
    with path.open("rb") as source:
        data = source.read(limit + 1)
    require(len(data) == info.st_size and not SECRET.search(data), "Changed input or possible secret in export")
    require(digest is None or hashlib.sha256(data).hexdigest() == digest, "Input changed since native verification")
    return data


def export_bundle(args):
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    report = output / "source-verification.report"
    run_native(args.engine, ["--addon-source-check", args.package, "--source-assets", args.source,
                            "--source-manifest", args.manifest, "--content-report", report], report)
    text = report.read_text(encoding="utf-8")
    match = re.search(r"^package ([a-z0-9_-]{1,31}) ([0-9]+\.[0-9]+\.[0-9]+) ([0-9a-f]{64})$", text, re.M)
    require(match is not None, "Missing native immutable package identity")
    addon, version, digest = match.groups()

    def put(name, data):
        relative(name)
        require(not SECRET.search(data), "Possible secret in export")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), "Duplicate bundle path")
        target.write_bytes(data)

    put(f"dist/{addon}.texelar", local_bytes(args.package, PACKAGE_LIMIT, digest))
    for asset, size, expected in re.findall(r"^source (\S+) (\d+) ([0-9a-f]{64})$", text, re.M):
        relative(asset)
        is_manifest = asset == f"addons/{addon}.addon"
        data = local_bytes(args.manifest if is_manifest else args.source / asset, 64 * 1024 * 1024, expected)
        require(len(data) == int(size), "Source byte count changed")
        put(f"manifest/{addon}.addon" if is_manifest else f"assets/{asset}", data)
    put("LICENSE", local_bytes(args.license, CATALOG_LIMIT))
    put("ATTRIBUTION.md", local_bytes(args.attribution, CATALOG_LIMIT))
    preview = local_bytes(args.preview, 262144)
    require(preview.startswith(b"\xff\xd8") and preview.endswith(b"\xff\xd9"), "Preview must be a bounded JPEG")
    put("previews/preview.jpg", preview)
    total = 0
    for index, path in enumerate(sorted(args.evidence.rglob("*"))):
        require(index < 4096, "Too many evidence files")
        if path.is_dir():
            continue
        require(path.suffix in {".report", ".trace", ".csv", ".jpg", ".lock"},
                "Evidence may contain reports, traces, CSV, JPEG and exact locks only")
        data = local_bytes(path, CATALOG_LIMIT)
        total += len(data)
        require(total <= FETCH_LIMIT, "Evidence ceiling exceeded")
        put("evidence/" + path.relative_to(args.evidence).as_posix(), data)
    require(total, "Frozen evidence is required")
    if args.inputs:
        total = 0
        for index, path in enumerate(sorted(args.inputs.rglob("*"))):
            require(index < 4096, "Too many authoring inputs")
            if path.is_dir():
                continue
            require(path.suffix in {".recipe", ".theme", ".intent", ".kit", ".scope"},
                    "Only native reproducible authoring inputs belong in the input export")
            data = local_bytes(path, CATALOG_LIMIT)
            total += len(data)
            require(total <= FETCH_LIMIT, "Authoring input ceiling exceeded")
            put("inputs/" + path.relative_to(args.inputs).as_posix(), data)
    put("README.md", (f"# {addon} {version}\n\n"
        "Editable source and frozen Texelar export. See LICENSE and ATTRIBUTION.md.\n"
        "Evidence is provenance; registry validation and human catalog/content review remain separate.\n").encode())
    put("SUBMIT.md", ("# Publish this directory\n\n"
        "Upload these files to your own public GitHub repository using Add file > Upload files.\n"
        "Commit them, then copy the full 40-character commit SHA.\n"
        "Fork TolinSimpson/texelar-mods and copy submissions/TEMPLATE.submission to\n"
        f"submissions/{addon}/{version}.submission. Fill in your repository, full commit and paths:\n\n"
        f"source assets\nmanifest manifest/{addon}.addon\npackage dist/{addon}.texelar\n"
        "license LICENSE\nattribution ATTRIBUTION.md\npreview previews/preview.jpg\nevidence evidence\n\n"
        "Open a pull request. No version is approved by export, a tag or a creator report.\n"
        "Review this directory for private files and secrets before uploading.\n").encode())
    put("bundle.report", (f"texelar-github-export 1\nid {addon}\nversion {version}\nsha256 {digest}\n"
        "state prepared-for-creator-review\npublication not-requested\n").encode())
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-submission")
    check.add_argument("submission", type=Path)
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("submission", type=Path)
    for command in (verify_parser, commands.add_parser("build")):
        command.add_argument("--root", type=Path, default=Path("."))
        command.add_argument("--engine", type=Path, required=True)
        command.add_argument("--base", type=Path, required=True)
        command.add_argument("--work", type=Path, required=True)
    build_parser = commands.choices["build"]
    build_parser.add_argument("--output", type=Path, required=True)
    build_parser.add_argument("--previous", type=Path)
    export = commands.add_parser("export")
    for field in ("engine", "package", "source", "manifest", "license", "attribution", "preview", "evidence", "output"):
        export.add_argument("--" + field, type=Path, required=True)
    export.add_argument("--inputs", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "check-submission":
            submission(args.submission)
            print("Submission framing accepted; package/ownership/review checks remain required.")
        elif args.command == "verify":
            print(verify(args.submission, args.root, args.work, args.engine, args.base))
        elif args.command == "build":
            print(build(args.root, args.output, args.engine, args.base, args.work, args.previous))
        else:
            print(export_bundle(args))
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"Catalog operation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
