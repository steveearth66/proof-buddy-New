"""
Run all expression_tree regression tests AND Django test suite.

Usage (from django_server/):
    py -m expression_tree.runTests
"""

import subprocess
import sys
import os

# ── 1. Plain-Python expression_tree tests ────────────────────────────────────
print("=" * 60)
print("expression_tree: testApplyRule")
print("=" * 60)
from . import testApplyRule  # noqa: F401 (runs on import)

print()
print("=" * 60)
print("expression_tree: testAdvMath")
print("=" * 60)
from . import testAdvMath  # noqa: F401

# ── 2. Django TestCase suite (proofs, induction_api, equational_reasoning_api,
#       accounts, assignments, racket_api, …) ──────────────────────────────────
print()
print("=" * 60)
print("Django manage.py test")
print("=" * 60)

# manage.py lives one level above this package (in django_server/)
manage_py_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
result = subprocess.run(
    [sys.executable, "manage.py", "test", "--verbosity=2"],
    cwd=manage_py_dir,
)

sys.exit(result.returncode)
