"""
Main test driver for Proof Buddy test suite.

Runs all test modules in sequence:
- test_math_operations: Math operations (+, -, *, quotient, remainder, expt) and comparisons
- test_logic_operations: Logic operations (not, and, or, xor, implies)
- test_list_operations: List operations (cons, first, rest) and predicates
- test_axioms_and_udfs: Axiom tests and user-defined function tests
- test_integration: Node methods, JSON, rewrite demonstrations, proof building
- test_induction: Full induction proof tests
- induction_api persistence database tests
- induction_api cross-mode name conflict tests

Run with: python manage.py test proofs
"""

from pathlib import Path
import subprocess
import sys

print("=" * 40)
print("PROOF BUDDY TEST SUITE")
print("=" * 40)
print()

# Import all test modules to execute them
from . import test_math_operations
from . import test_logic_operations
from . import test_list_operations
from . import test_axioms_and_udfs
from . import test_integration
from . import test_induction

# Collect total failures from all modules
totalFails = 0
totalFails += test_math_operations.totalFails
totalFails += test_logic_operations.totalFails
totalFails += test_list_operations.totalFails
totalFails += test_axioms_and_udfs.totalFails
totalFails += test_integration.totalFails
totalFails += test_induction.totalFails


def run_command(name: str, cmd: list[str], cwd: Path) -> int:
    """Run an external command; return 0 on success, else exit code."""
    try:
        print(f"\n[Summary] {name}")
        result = subprocess.run(cmd, cwd=cwd, text=True)
        if result.returncode == 0:
            print(f"PASS: {name}")
        else:
            print(f"FAIL: {name} (exit {result.returncode})")
        return result.returncode
    except FileNotFoundError as exc:
        print(f"FAIL: {name} not run (missing binary): {exc}")
        return 1


root_dir = Path(__file__).resolve().parents[1]  # django_server
project_root = root_dir.parent  # repository root

persistence_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_database_persistence",
]
persistence_failures = run_command("Database persistence", persistence_cmd, cwd=root_dir)

totalFails += (1 if persistence_failures else 0)

name_conflict_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.tests_name_conflict",
]
name_conflict_failures = run_command("Cross-mode name conflict", name_conflict_cmd, cwd=root_dir)

totalFails += (1 if name_conflict_failures else 0)

error_persistence_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_error_persistence",
]
error_persistence_failures = run_command("Induction error persistence case isolation", error_persistence_cmd, cwd=root_dir)

totalFails += (1 if error_persistence_failures else 0)

is_complete_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.tests_is_complete_persistence",
]
is_complete_failures = run_command("InductionProof is_complete persistence", is_complete_cmd, cwd=root_dir)

totalFails += (1 if is_complete_failures else 0)

print()
print("=" * 40)
print("TEST SUITE SUMMARY")
print("=" * 40)
if totalFails == 0:
    print("\nAll tests passed!\n")
else:
    print(f"\nTotal failures: {totalFails}\n")
