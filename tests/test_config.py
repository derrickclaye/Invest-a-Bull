from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from invest_a_bull.config import AnalysisConfig, resolve_project_root
import invest_a_bull.config as config_module


class ConfigTests(unittest.TestCase):
    def test_resolve_project_root_uses_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            override_root = Path(temp_dir)
            with patch.dict(os.environ, {"INVEST_A_BULL_PROJECT_ROOT": str(override_root)}, clear=False):
                self.assertEqual(resolve_project_root(), override_root.resolve())
                self.assertEqual(AnalysisConfig().project_root, override_root.resolve())

    def test_resolve_project_root_detects_repo_from_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (repo_root / "src" / "invest_a_bull").mkdir(parents=True)
            nested_workdir = repo_root / "scripts" / "daily"
            nested_workdir.mkdir(parents=True)

            original_cwd = Path.cwd()
            try:
                os.chdir(nested_workdir)
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(resolve_project_root(), repo_root.resolve())
                    self.assertEqual(AnalysisConfig().project_root, repo_root.resolve())
            finally:
                os.chdir(original_cwd)

    def test_resolve_project_root_raises_when_no_checkout_can_be_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            isolated_dir = Path(temp_dir)
            fake_package_root = isolated_dir / "site-packages" / "invest_a_bull"
            fake_package_root.mkdir(parents=True)
            fake_config_path = fake_package_root / "config.py"
            fake_config_path.write_text("# stub\n", encoding="utf-8")

            original_cwd = Path.cwd()
            try:
                os.chdir(isolated_dir)
                with (
                    patch.dict(os.environ, {}, clear=True),
                    patch.object(config_module, "__file__", str(fake_config_path)),
                ):
                    with self.assertRaisesRegex(RuntimeError, "INVEST_A_BULL_PROJECT_ROOT"):
                        resolve_project_root()
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()

