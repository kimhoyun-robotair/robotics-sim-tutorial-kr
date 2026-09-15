"""공식 출처 대응표, 패키지 내부 경로, 독립 실행 진입점의 회귀 검사."""
# pyright: reportUninitializedInstanceVariable=false

import ast
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SPEC = importlib.util.spec_from_file_location("catalog", SRC / "catalog.py")
assert SPEC is not None and SPEC.loader is not None
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


class CatalogValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        package = self.root / "00_example"
        package.mkdir()
        row: dict[str, Any] = {
            "id": "t001", "title": "Example", "category": "core",
            "source_path": "core/example.html", "package": "src/00_example",
            "source_url": "https://docs.isaacsim.omniverse.nvidia.com/5.1.0/core/example.html",
            "learning_order": 0, "learning_stage": "intro",
        }
        self.inventory: dict[str, Any] = {
            "tutorials": [row],
            "navigation_audit": [{"source_path": row["source_path"], "disposition": "package"}],
            "learning_stages": [{"key": "intro", "tutorial_ids": ["t001"]}],
        }
        self.metadata: dict[str, Any] = {
            **row, "mode": "standalone", "entrypoint": "run.py",
            "artifacts": ["run.py", "TUTORIAL.md"],
            "requirements": ["Isaac Sim 5.1.0"], "verification": "not_run",
        }
        (package / "TUTORIAL.md").write_text(row["source_url"], encoding="utf-8")
        (package / "run.py").write_text("print('example')\n", encoding="utf-8")
        self.write_fixture()

    def tearDown(self):
        self.temp.cleanup()

    def write_fixture(self):
        (self.root / "official_tutorials.json").write_text(json.dumps(self.inventory), encoding="utf-8")
        (self.root / "00_example" / "tutorial.json").write_text(json.dumps(self.metadata), encoding="utf-8")

    def test_complete_package_is_accepted(self):
        self.assertEqual(catalog.check_catalog(self.root), [])

    def test_missing_entrypoint_is_reported(self):
        (self.root / "00_example" / "run.py").unlink()
        self.assertTrue(any("run.py" in error for error in catalog.check_catalog(self.root)))

    def test_reference_cannot_escape_copied_package(self):
        self.metadata["artifacts"] = ["../shared.py"]
        (self.root / "shared.py").write_text("", encoding="utf-8")
        self.write_fixture()
        self.assertTrue(any("상대 경로" in error for error in catalog.check_catalog(self.root)))

    def test_symlink_cannot_escape_package(self):
        outside = self.root / "shared.py"
        outside.write_text("", encoding="utf-8")
        (self.root / "00_example" / "outside.py").symlink_to(outside)
        self.metadata["artifacts"] = ["outside.py"]
        self.write_fixture()
        self.assertTrue(any("패키지 밖" in error for error in catalog.check_catalog(self.root)))

    def test_changed_version_source_is_reported(self):
        self.metadata["source_url"] = self.metadata["source_url"].replace("5.1.0", "latest")
        self.write_fixture()
        self.assertTrue(any("source_url" in error for error in catalog.check_catalog(self.root)))

    def test_duplicate_official_page_is_reported(self):
        self.inventory["tutorials"].append(dict(self.inventory["tutorials"][0]))
        self.write_fixture()
        self.assertTrue(any("중복" in error for error in catalog.check_catalog(self.root)))

    def test_navigation_omission_is_reported(self):
        self.inventory["navigation_audit"] = []
        self.write_fixture()
        self.assertTrue(any("목차 감사" in error for error in catalog.check_catalog(self.root)))

    def test_unindexed_package_is_reported(self):
        extra = self.root / "forgotten"
        extra.mkdir()
        (extra / "tutorial.json").write_text("{}", encoding="utf-8")
        self.assertTrue(any("forgotten" in error for error in catalog.check_catalog(self.root)))

    def test_learning_order_must_be_contiguous(self):
        self.inventory["tutorials"][0]["learning_order"] = 1
        self.metadata["learning_order"] = 1
        self.write_fixture()
        errors = catalog.check_catalog(self.root)
        self.assertTrue(any("누락·중복" in error for error in errors))
        self.assertTrue(any("폴더 이름의 번호" in error for error in errors))

    def test_manifest_order_must_match_inventory(self):
        self.metadata["learning_order"] = 1
        self.write_fixture()
        self.assertTrue(any("learning_order" in error for error in catalog.check_catalog(self.root)))

    def test_stage_members_must_match_learning_order(self):
        self.inventory["learning_stages"][0]["tutorial_ids"] = []
        self.write_fixture()
        self.assertTrue(any("학습 단계의 튜토리얼 순서" in error for error in catalog.check_catalog(self.root)))


class RepositoryPackagesTests(unittest.TestCase):
    def test_official_inventory_and_all_packages_agree(self):
        self.assertEqual(catalog.check_catalog(SRC), [])

    def test_python_sources_have_no_shared_tutorial_import(self):
        rows = catalog.read_inventory()["tutorials"]
        forbidden = {Path(row["package"]).name for row in rows} | {"tutorial_common"}
        forbidden |= {re.sub(r"^\d+_", "", name) for name in forbidden}
        for row in rows:
            package = catalog.package_path(SRC, row["package"])
            for path in package.rglob("*.py"):
                if "output" in path.relative_to(package).parts:
                    continue
                with self.subTest(path=str(path.relative_to(ROOT))):
                    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            names = [alias.name.split(".")[0] for alias in node.names]
                        elif isinstance(node, ast.ImportFrom) and node.level == 0:
                            names = [(node.module or "").split(".")[0]]
                        else:
                            continue
                        self.assertFalse(set(names) & forbidden, f"다른 튜토리얼 import: {path}:{node.lineno}")

    def test_catalog_lists_numeric_order_and_resolves_both_identifiers(self):
        listed = subprocess.run(
            [sys.executable, str(SRC / "catalog.py"), "list"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        self.assertEqual([line.split("\t")[0] for line in listed], [f"{n:02d}" for n in range(180)])
        self.assertEqual([line.split("\t")[1] for line in listed[:3]], ["t001", "t098", "t099"])
        outputs = []
        for identifier in ("01", "t098", "01_core_core_hello_world"):
            outputs.append(subprocess.run(
                [sys.executable, str(SRC / "catalog.py"), "show", identifier],
                capture_output=True, text=True, check=True,
            ).stdout)
        self.assertTrue(all(text == outputs[0] for text in outputs))
        self.assertIn("Hello World", outputs[0])

    def test_standalone_help_from_isolated_package(self):
        for row in catalog.read_inventory()["tutorials"]:
            package = catalog.package_path(SRC, row["package"])
            metadata = json.loads((package / "tutorial.json").read_text(encoding="utf-8"))
            entrypoint = metadata.get("entrypoint")
            if metadata["mode"] != "standalone" or not entrypoint or not entrypoint.endswith(".py"):
                continue
            with self.subTest(package=package.name), tempfile.TemporaryDirectory() as directory:
                copied = Path(directory) / package.name
                shutil.copytree(package, copied, ignore=shutil.ignore_patterns("output", "__pycache__"))
                result = subprocess.run(
                    [sys.executable, str(copied / entrypoint), "--help"],
                    cwd=directory, capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
