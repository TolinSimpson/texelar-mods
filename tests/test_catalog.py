import copy
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import catalog
import previous


def record():
    return {"repository": "Creator/arena", "commit": "a" * 40,
            "manifest": "manifest/arena.addon", "package": "dist/arena.texelar", "bytes": "123",
            "sha256": "b" * 64, "review": "approved", "tags": "arena",
            "evidence": "Independent native/runtime checks; human review remains separate.",
            "changes": "First version.", "report": "https://github.com/Creator/arena/issues",
            "meta": ["texelar-addon 2", "id arena", "title Arena", "version 1.0.0",
                     "game showcase", "api 1.0.0", "author Creator", "license MIT", "kind community",
                     "redistribute yes"]}


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_untrusted_paths_and_origins(self):
        for value in ("../secret", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a:b",
                      "a/%2e%2e", "a/NUL.txt", "a/con", "a/.env", "a/end."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog.relative(value)
        for value in ("Creator/repo/extra", "user@host/repo", "../repo", "owner/repo?token=x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                catalog.repository(value)
        self.assertEqual(catalog.relative("assets/levels/arena.level"), "assets/levels/arena.level")

    def test_exact_commits_only(self):
        for value in ("main", "v1.0.0", "abcdef", "A" * 40, "a" * 40 + "/x"):
            with self.assertRaises(ValueError):
                catalog.commit(value)

    def test_round_trip_and_truncation(self):
        path = self.root / "library.catalog"
        catalog.write_catalog([record()], path, 1)
        self.assertEqual(catalog.parse_catalog(path), (1, [record()]))
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            catalog.parse_catalog(path)

    def test_duplicate_versions_and_metadata(self):
        path = self.root / "library.catalog"
        catalog.write_catalog([record(), record()], path, 1)
        with self.assertRaises(ValueError):
            catalog.parse_catalog(path)
        bad = record()
        bad["meta"].append("id impersonation")
        with self.assertRaises(ValueError):
            catalog.identity(bad)

    def test_package_ceiling_and_reserved_identity(self):
        path = self.root / "library.catalog"
        bad = record()
        bad["bytes"] = str(catalog.PACKAGE_LIMIT + 1)
        catalog.write_catalog([bad], path, 1)
        with self.assertRaises(ValueError):
            catalog.parse_catalog(path)
        for name in ("base", "official", "texelar", "engine"):
            bad = record()
            bad["meta"][1] = "id " + name
            with self.assertRaises(ValueError):
                catalog.identity(bad)

    def test_unknown_fields_rejected(self):
        path = self.root / "library.catalog"
        catalog.write_catalog([record()], path, 1)
        path.write_text(path.read_text().replace("end\n", "execute powershell\nend\n"))
        with self.assertRaises(ValueError):
            catalog.parse_catalog(path)

    def test_pending_cannot_publish(self):
        path = self.root / "records/arena/1.0.0.catalog"
        pending = record()
        pending["review"] = "pending"
        catalog.write_catalog([pending], path, 1)
        with self.assertRaisesRegex(ValueError, "Pending"):
            catalog.build(self.root, self.root / "out.catalog", "engine", "base", self.root / "work")

    def test_publication_retains_tombstones(self):
        previous_path = self.root / "previous.catalog"
        catalog.write_catalog([record()], previous_path, 1)
        with self.assertRaisesRegex(ValueError, "tombstones"):
            catalog.build(self.root, self.root / "out.catalog", "engine", "base", self.root / "work", previous_path)

    def test_published_version_bytes_immutable(self):
        old = self.root / "previous.catalog"
        catalog.write_catalog([record()], old, 1)
        changed = record()
        changed["sha256"] = "c" * 64
        catalog.write_catalog([changed], self.root / "records/arena/1.0.0.catalog", 2)
        with patch.object(catalog, "ownership"), self.assertRaisesRegex(ValueError, "Immutable"):
            catalog.build(self.root, self.root / "out.catalog", "engine", "base", self.root / "work", old)

    def test_deleted_upstream_can_be_blocked_without_redownload(self):
        old = self.root / "previous.catalog"
        catalog.write_catalog([record()], old, 1)
        blocked = record()
        blocked["review"] = "blocked"
        catalog.write_catalog([blocked], self.root / "records/arena/1.0.0.catalog", 2)
        with patch.object(catalog, "ownership"), patch.object(catalog, "run_native"), patch.object(catalog, "verify") as verify:
            catalog.build(self.root, self.root / "out.catalog", "engine", "base", self.root / "work", old)
            verify.assert_not_called()
        self.assertEqual(catalog.parse_catalog(self.root / "out.catalog")[1][0]["review"], "blocked")

    def test_secret_rejected_before_export(self):
        path = self.root / "evidence.report"
        path.write_bytes(b"ghp_" + b"a" * 36)
        with self.assertRaisesRegex(ValueError, "secret"):
            catalog.local_bytes(path, 1024)

    def test_local_source_changed_after_verification(self):
        path = self.root / "arena.level"
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            catalog.local_bytes(path, 1024, hashlib.sha256(b"original").hexdigest())

    def test_previous_unavailable_is_not_first_publication(self):
        for status in (403, 404, 429, 500):
            error = urllib.error.HTTPError("https://api.github.com/test", status, "fixture", {}, None)
            with patch.object(previous, "api", side_effect=error), self.assertRaises(ValueError):
                previous.previous("Creator/catalog", self.root / "previous.catalog")
        error = urllib.error.HTTPError("https://api.github.com/test", 404, "fixture", {}, None)
        with patch.object(previous, "api", side_effect=error):
            self.assertFalse(previous.previous("Creator/catalog", self.root / "previous.catalog", True))

    def test_workflow_credentials_and_trusted_checkout(self):
        root = Path(__file__).resolve().parents[1]
        validate = (root / ".github/workflows/submissions.yml").read_text()
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", validate)
        self.assertIn("contents: read", validate)
        self.assertIn("persist-credentials: false", validate)
        self.assertNotIn("secrets.", validate)
        self.assertNotIn("pull_request.head", validate)
        publish = (root / ".github/workflows/publish.yml").read_text()
        self.assertIn("environment: catalog-publication", publish)
        self.assertIn("required_reviewers", publish)
        self.assertIn("needs: verify", publish)


if __name__ == "__main__":
    unittest.main()
