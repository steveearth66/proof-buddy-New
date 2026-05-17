"""
Proof Buddy test suite.

All test modules are discovered and run once by Django's standard test
discovery.  Coloured FAIL/ERROR output is provided by the custom runner
registered in settings.py:

  TEST_RUNNER = 'proofs.runner.ColorDiscoverRunner'

Plain-Python test modules (test_math_operations, test_logic_operations, etc.)
execute their assertions at import time; Django imports them during discovery
and finds no TestCase subclasses, but the module-level checks still run.

Django TestCase/TransactionTestCase modules (induction_api/*, racket_api/*,
equational_reasoning_api/*, proofs/test_udf_if_type_mismatch, etc.) are
discovered and run normally by Django.
"""

