# Proof Buddy Test Suite

## Overview

The test suite has been refactored into a modular structure for better organization and maintainability.

## Test File Organization

### Main Driver
- **tests.py** - Main test driver that imports and runs all test modules

### Helper Module
- **test_helpers.py** - Common test utilities and helper functions:
  - `show_node_ids()` - Display node IDs for debugging
  - `find_node_id_by_data()` - Find node by data value
  - `find_call_node_id()` - Find function call nodes
  - `do_single_test_case()` - Run a single test case
  - `run_test_cases()` - Run multiple test cases with a single rule
  - `test_racket_function()` - Test Racket built-in functions
  - `test_axiom()` - Test axioms

### Test Modules

#### test_math_operations.py
Tests for basic math operations and comparison operators:
- Arithmetic: `+`, `-`, `*`, `quotient`, `remainder`, `expt`
- Comparisons: `=`, `<`, `<=`, `>`, `>=`
- Error cases: type mismatches, wrong argument counts, generic arguments

#### test_logic_operations.py
Tests for logic operations:
- `not`, `and`, `or`, `xor`, `implies`
- Error cases and edge cases for each operator

#### test_list_operations.py
Tests for list operations and predicates:
- List functions: `cons`, `first`, `rest`
- Predicates: `zero?`, `null?`, `if`, `integer?`, `list?`
- Type checking and error handling

#### test_axioms_and_udfs.py
Tests for axioms and user-defined functions:
- Axioms: `cons-first-rest`, `first-cons`, `rest-cons`, `-+`, `null?-cons`, `zero?+`, `and`, `or`, `implies`, `integer?`, `list?`
- UDF (User-Defined Functions) tests
- Parameter mapping and validation

#### test_integration.py
Integration tests for the proof engine:
- Node method tests (`funcset`, `ancestors`, `allMath`, `mathStr`, `logicStr`)
- JSON generation tests
- Position dictionary tests
- Proof building demonstrations
- Math rewrite tests
- Quotient floor division tests

#### test_induction.py
Complete induction proof tests:
- Base case proof construction (LHS and RHS)
- Induction hypothesis building
- Leap step proof construction (LHS and RHS)
- Full induction proof validation
- Reading test parameters from `indTest.txt`

## Running Tests

### Run All Tests
```bash
cd django_server
python manage.py test proofs
```

### Run Individual Test Modules
```bash
python manage.py test proofs.test_math_operations
python manage.py test proofs.test_logic_operations
python manage.py test proofs.test_list_operations
python manage.py test proofs.test_axioms_and_udfs
python manage.py test proofs.test_integration
python manage.py test proofs.test_induction
```

### Import Directly (for debugging)
```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_server.settings')
django.setup()

from proofs import test_math_operations
print(f"Math tests: {test_math_operations.totalFails} failures")
```

## Test Output

Each module tracks failures in a `totalFails` variable. The main driver collects these and provides a summary:

```
================================================================================
PROOF BUDDY TEST SUITE
================================================================================

[Summary] Math Operations Tests
... test output ...

[Summary] Logic Operations Tests  
... test output ...

================================================================================
TEST SUITE SUMMARY
================================================================================

✓ All tests passed!
```

## Benefits of Modular Structure

1. **Easier Navigation** - Find specific tests by category
2. **Faster Development** - Run only relevant tests during development
3. **Better Organization** - Related tests grouped together
4. **Maintainability** - Easier to update and extend specific test categories
5. **Parallel Testing** - Modules can be run independently
6. **Clear Dependencies** - Helper functions centralized in one place

## Previous Structure

The original `tests.py` was 1648 lines containing all tests in a single file.

## Current Structure

- **tests.py**: 44 lines (main driver)
- **test_helpers.py**: 118 lines (shared utilities)
- **test_math_operations.py**: 240 lines
- **test_logic_operations.py**: 106 lines
- **test_list_operations.py**: 154 lines
- **test_axioms_and_udfs.py**: 372 lines
- **test_integration.py**: 300+ lines
- **test_induction.py**: 500+ lines

Total: ~1800 lines (organized and modular)
