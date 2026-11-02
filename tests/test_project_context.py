import os
from pathlib import Path
import subprocess
import sys
import unittest


class ProjectContextIntegrationTests(unittest.TestCase):
    def test_isolated_asset_suite(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", "plugins/project-context/tests/test_project_context.py"],
                                cwd=root, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
