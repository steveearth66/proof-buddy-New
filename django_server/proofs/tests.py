"""
Main test driver for Proof Buddy test suite.

Runs all test modules in sequence:
- test_math_operations: Math operations (+, -, *, quotient, remainder, expt) and comparisons
- test_logic_operations: Logic operations (not, and, or, xor, implies)
- test_list_operations: List operations (cons, first, rest) and predicates
- test_axioms_and_udfs: Axiom tests and user-defined function tests
- test_integration: Node methods, JSON, rewrite demonstrations, proof building
- test_induction: Full induction proof tests
- induction_api.tests: Induction proof view and engine endpoint tests
- induction_api.test_database_persistence: DB persistence
- induction_api.test_proof_line_persistence: Proof line persistence
- induction_api.test_proof_management: Clear/new proof management
- induction_api.tests_name_conflict: Cross-mode name conflict
- induction_api.test_error_persistence: Error persistence case isolation
- induction_api.tests_is_complete_persistence: is_complete persistence
- induction_api.test_wrong_highlight: Wrong-highlight IndexError regression
- induction_api.test_lemma_param_generics: Lemma param generics exclusion regression
- induction_api.tests_proof_card_fields: Proof card goal fields (list endpoint)
- test_manual_persistence: Manual proof line DB persistence
- equational_reasoning_api.tests: EquationalProof model and serializer tests
- equational_reasoning_api.test_integration: Equational reasoning API integration
- equational_reasoning_api.test_set_parameters: ER set-parameters feature tests
- equational_reasoning_api.test_value_mapping: Value Mapping (High support) engine and API tests

Run with: python manage.py test proofs
"""

from pathlib import Path
import subprocess
import sys
import os

_RED   = "\x1b[1;31m" if sys.stdout.isatty() else ""
_RESET = "\x1b[0m"    if sys.stdout.isatty() else ""
_failed_sections: list[str] = []

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
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(cmd, cwd=cwd, text=True, env=env)
        if result.returncode == 0:
            print(f"PASS: {name}")
        else:
            print(f"{_RED}FAIL: {name} (exit {result.returncode}){_RESET}")
            _failed_sections.append(name)
        return result.returncode
    except FileNotFoundError as exc:
        print(f"{_RED}FAIL: {name} not run (missing binary): {exc}{_RESET}")
        _failed_sections.append(name)
        return 1


root_dir = Path(__file__).resolve().parents[1]  # django_server
project_root = root_dir.parent  # repository root

persistence_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.tests",
]
induction_api_tests_failures = run_command("Induction API view and engine endpoint tests", persistence_cmd, cwd=root_dir)

totalFails += (1 if induction_api_tests_failures else 0)

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

proof_line_persistence_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_proof_line_persistence",
]
proof_line_persistence_failures = run_command("Proof line persistence", proof_line_persistence_cmd, cwd=root_dir)

totalFails += (1 if proof_line_persistence_failures else 0)

proof_management_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_proof_management",
]
proof_management_failures = run_command("Proof management (clear/new)", proof_management_cmd, cwd=root_dir)

totalFails += (1 if proof_management_failures else 0)

eq_model_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "equational_reasoning_api.tests",
]
eq_model_failures = run_command("Equational reasoning model and serializer tests", eq_model_cmd, cwd=root_dir)

totalFails += (1 if eq_model_failures else 0)

eq_integration_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "equational_reasoning_api.test_integration",
]
eq_integration_failures = run_command("Equational reasoning API integration", eq_integration_cmd, cwd=root_dir)

totalFails += (1 if eq_integration_failures else 0)

udf_in_udf_cmd = [
    sys.executable,
    "-c",
    (
        "import django, os; "
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_server.settings'); "
        "django.setup(); "
        "exec(open('proofs/test_udf_in_udf.py').read())"
    ),
]
udf_in_udf_failures = run_command(
    "UDF-calls-UDF arg-count tests",
    udf_in_udf_cmd,
    cwd=root_dir,
)
totalFails += (1 if udf_in_udf_failures else 0)

lemma_app_cmd = [
    sys.executable,
    "-c",
    (
        "import django, os; "
        "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_server.settings'); "
        "django.setup(); "
        "exec(open('proofs/test_lemma_application.py').read())"
    ),
]
# Run from the django_server directory so the relative open() path works
lemma_app_failures = run_command(
    "LemmaRule / LemmaApplicator engine tests",
    lemma_app_cmd,
    cwd=root_dir,
)
totalFails += (1 if lemma_app_failures else 0)

wrong_highlight_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_wrong_highlight",
]
wrong_highlight_failures = run_command(
    "Wrong-highlight IndexError regression",
    wrong_highlight_cmd,
    cwd=root_dir,
)
totalFails += (1 if wrong_highlight_failures else 0)

lemma_param_generics_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.test_lemma_param_generics",
]
lemma_param_generics_failures = run_command(
    "Lemma param generics exclusion regression",
    lemma_param_generics_cmd,
    cwd=root_dir,
)
totalFails += (1 if lemma_param_generics_failures else 0)

proof_card_fields_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "induction_api.tests_proof_card_fields",
]
proof_card_fields_failures = run_command(
    "Proof card goal fields (list endpoint)",
    proof_card_fields_cmd,
    cwd=root_dir,
)
totalFails += (1 if proof_card_fields_failures else 0)

manual_persistence_cmd = [
    sys.executable,
    "manage.py",
    "test",
    "test_manual_persistence",
]
manual_persistence_failures = run_command(
    "Manual proof line persistence",
    manual_persistence_cmd,
    cwd=root_dir,
)
totalFails += (1 if manual_persistence_failures else 0)

eq_set_params_cmd = [sys.executable, "manage.py", "test", "equational_reasoning_api.test_set_parameters"]
eq_set_params_failures = run_command("ER set-parameters feature tests", eq_set_params_cmd, cwd=root_dir)
totalFails += (1 if eq_set_params_failures else 0)

eq_value_mapping_cmd = [sys.executable, "manage.py", "test", "equational_reasoning_api.test_value_mapping"]
eq_value_mapping_failures = run_command("Value Mapping (High support) engine and API tests", eq_value_mapping_cmd, cwd=root_dir)
totalFails += (1 if eq_value_mapping_failures else 0)

ind_set_params_cmd = [sys.executable, "manage.py", "test", "induction_api.test_set_parameters"]
ind_set_params_failures = run_command("Induction set-parameters feature tests", ind_set_params_cmd, cwd=root_dir)
totalFails += (1 if ind_set_params_failures else 0)

print()
print("=" * 40)
print("TEST SUITE SUMMARY")
print("=" * 40)
if totalFails == 0:
    print("\nAll tests passed!\n")
else:
    print(f"\n{_RED}Total failures: {totalFails}{_RESET}\n")
    if _failed_sections:
        print(f"{_RED}Failing sections:{_RESET}")
        for _s in _failed_sections:
            print(f"  {_RED}- {_s}{_RESET}")
        print()
