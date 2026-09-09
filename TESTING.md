# Proof Buddy Testing Guide

This document explains how every automated test in the repository is run, and briefly describes what each test file covers.

Manual browser smoke tests for equational reasoning live in [TESTING_MANUAL_QA.md](TESTING_MANUAL_QA.md). Older notes that only cover the `proofs/` engine modules live in [django_server/proofs/TEST_STRUCTURE.md](django_server/proofs/TEST_STRUCTURE.md).

---

## Overview

Proof Buddy has four kinds of tests:

| Kind | Runner | Needs a live server? | Needs MySQL? |
|---|---|---|---|
| Django `TestCase` / `APITestCase` modules | `python manage.py test` | No | Yes (creates a separate `test_proofbuddy` database) |
| Import-time Python scripts (no `TestCase` classes) | Imported by Django discovery, or run as `python -m …` | No | Only if Django discovery imports them |
| Jest / React Testing Library | `npm test` in `client/` | No | No |
| Live-server scripts (HTTP or Puppeteer) | Run the file directly | Yes | Yes (the real app database) |

There is no CI pipeline. Tests are run locally.

---

## Prerequisites

- Python virtualenv activated, with `django_server/requirements.txt` installed
- MySQL running, and a project-root `.env` with `DB_*` values
- Node.js / npm, with `client/node_modules` installed (`cd client && npm install`)

Django tests use a **separate** MySQL database named `test_proofbuddy` (`DATABASES['default']['TEST']['NAME']` in `django_server/django_server/settings.py`). They should not write to the development database.

### Windows encoding

Several tests print Unicode rule text (`↦`). In PowerShell, set this before Django test commands:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

Then run tests from `django_server/`:

```powershell
cd django_server
py manage.py test
```

---

## How to run the suites

### Run almost everything (expression engine + Django + Jest)

From `django_server/`:

```powershell
$env:PYTHONIOENCODING = "utf-8"
py -m expression_tree.runTests
```

`expression_tree/runTests.py` does three things in order:

1. Imports `expression_tree.testApplyRule` and `expression_tree.testAdvMath` (they run on import)
2. Runs `python manage.py test --verbosity=2` (all Django apps)
3. Runs `npx jest --no-coverage` in `client/`

It does **not** run the live-server scripts (`test_equational_api.py`, `trial-automation.js`) or the skipped `expression_tree` files.

### Backend — all Django tests

From `django_server/`:

```powershell
$env:PYTHONIOENCODING = "utf-8"
py manage.py test
```

Django discovers `test*.py` and `tests.py` under installed apps (`accounts`, `racket_api`, `proofs`, `induction_api`, `equational_reasoning_api`, `assignments`). The custom runner `proofs.runner.ColorDiscoverRunner` only adds red FAIL/ERROR coloring.

Run one app or one module:

```powershell
py manage.py test proofs
py manage.py test induction_api
py manage.py test equational_reasoning_api
py manage.py test assignments
py manage.py test racket_api

py manage.py test induction_api.test_check_complete
py manage.py test equational_reasoning_api.test_value_mapping
```

Useful flags: `--verbosity=2`, `--keepdb` (reuse `test_proofbuddy` instead of recreating it).

### Backend — expression-tree scripts (not Django TestCases)

These files assert by printing PASS/FAIL as they execute. They are **not** collected as Django tests unless some other Django module imports them.

From `django_server/`:

```powershell
py -m expression_tree.testApplyRule
py -m expression_tree.testAdvMath
py -m expression_tree.test_rule_subclasses
py -m expression_tree.test_rule_edge_cases
```

`py -m pytest expression_tree/testApplyRule.py` appears in older docs. **pytest is not a project dependency.** Prefer the `python -m` commands above.

### Frontend — Jest

From `client/`:

```powershell
npm test
```

That script runs Jest with a larger Node heap (`NODE_OPTIONS=--max-old-space-size=4096`). Config is `client/jest.config.js` (jsdom, Babel, CSS/image mocks, `src/setupTests.js`).

```powershell
npm test -- --watch
npm test -- --coverage
npm test -- --testPathPattern=InductionRacket
npm test -- --testPathPattern=playMode
npm test -- --testPathPattern=EquationalReasoningNew
```

Jest picks up `*.test.js` files. Frontend tests mock HTTP and layout, so the Django server does **not** need to be running.

### Live-server / browser scripts

These hit a running app. Start Django (`localhost:8000`) and, for Puppeteer, the React dev server (`localhost:3000`).

```powershell
# From repo root — HTTP smoke of equational endpoints (auth is not configured in the script)
py test_equational_api.py

# From repo root — start both servers, then drive induction UI with Puppeteer
.\trial.ps1
```

`trial.ps1` launches the two servers and then `node trial-automation.js`. Puppeteer is a root `package.json` dependency (`npm install` at the repo root if needed).

### Manual browser QA

Follow [TESTING_GUIDE.md](TESTING_GUIDE.md) against `http://localhost:3000/equational-reasoning`. Course UI checks are listed in [COURSE_DEVELOPER_NOTES.md](documentation/user_documentation/Courses/COURSE_DEVELOPER_NOTES.md).

---

## How Django discovery interacts with import-time tests

Several `proofs/test_*.py` files are **not** `django.test.TestCase` classes. They run their assertions at **import time**. When Django discovers `proofs/`, it imports those modules, so the checks still execute, even though Django may report “Ran 0 tests” for that file.

`proofs/tests.py` is only a short comment; it no longer orchestrates other modules. Discovery plus `ColorDiscoverRunner` is the runner.

`django_server/test_manual_persistence.py` sits next to `manage.py`, not inside an app. `py manage.py test` (no label) will **not** pick it up. Run it explicitly:

```powershell
py manage.py test test_manual_persistence
```

---

## Frontend test files

Support files (not test suites): `client/src/setupTests.js` (jest-dom, `ResizeObserver` and `sessionStorage` stubs) and `client/src/__mocks__/fileMock.js` (static-asset stub).

| File | What it tests |
|---|---|
| `client/src/App.test.js` | Smoke: `App` renders without throwing. |
| `client/src/test/EquationalReasoningNew.test.js` | Equational Reasoning page UI with services and heavy children mocked: headings, name/tag/goal fields, typing, start-form validation (missing name/goals, identical LHS/RHS, reserved names), and the start confirmation modal. |
| `client/src/test/InductionRacket.test.js` | Induction page UI with the same mock pattern: headings, integer/list radios, induction parameters, goal fields, typing, validation (anchor value, leap vs induction variable, leap in a goal, missing IH, reserved names), and the start confirmation modal. |
| `client/src/test/playMode.test.js` | Pure unit tests of `playModeUtils.js` (no React): init, advance, cancel, visibility, Continue-button logic, and independence of induction case/side slots. Also includes a manual UI checklist in comments. |
| `client/src/test/playModeFeatures.test.js` | Play Mode UI: “Run Proof” on proof cards, premise-only edge case, footer greying vs Continue, row-number click blocking, full advance/cancel lifecycles, and independent base/leap × LHS/RHS state. |

---

## Django app: `proofs/` (expression engine, mostly import-time)

| File | What it tests |
|---|---|
| `proofs/tests.py` | Not a suite. Documents that Django discovery plus `ColorDiscoverRunner` is the runner. |
| `proofs/test_helpers.py` | Shared helpers (`do_single_test_case`, `test_racket_function`, `test_axiom`, node-id utilities). Not a suite by itself. |
| `proofs/test_math_operations.py` | Import-time: `+`, `-`, `*`, `quotient`, `remainder`, `expt` and comparisons; arity, types, generics, unresolved args. |
| `proofs/test_logic_operations.py` | Import-time: `not`, `and`, `or`, `xor`, `implies` and error cases. |
| `proofs/test_list_operations.py` | Import-time: `cons`, `first`, `rest` and predicates (`zero?`, `null?`, `if`, `integer?`, `list?`). |
| `proofs/test_axioms_and_udfs.py` | Import-time: axiom parameter mapping, built-in axioms, and UDF definition/application. |
| `proofs/test_integration.py` | Import-time: node methods, JSON/position helpers, proof-building and math-rewrite demos. |
| `proofs/test_induction.py` | Import-time: a full integer induction proof (base + leap, both sides), driven by `proofs/indTest.txt`. |
| `proofs/test_lemma_application.py` | Import-time, no DB: `LemmaRule` / `LemmaApplicator` (param counts, names, highlight, happy paths). |
| `proofs/test_udf_in_udf.py` | Import-time: UDFs that call other UDFs (e.g. `rev` calling `append`) use the callee’s signature. |
| `proofs/test_udf_if_type_mismatch.py` | Django `TestCase`: UDF `if` branches with mismatched types are rejected; `?` in UDF labels. |
| `proofs/indTest.txt` | Input data for `test_induction.py`, not a test file. |
| `proofs/runner.py` | Custom Django test runner (colorized FAIL/ERROR). Not a test file. |

---

## Django app: `equational_reasoning_api/`

| File | What it tests |
|---|---|
| `equational_reasoning_api/tests.py` | `EquationalProof` / `EquationalProofLine` models and serializer validation (empty or identical goals). |
| `equational_reasoning_api/test_integration.py` | Authenticated HTTP walkthrough of the main equational endpoints. |
| `equational_reasoning_api/test_set_parameters.py` | Support-parameter fields on the model and `PATCH /set-parameters` (instructor vs student, get-proof-lines payload). |
| `equational_reasoning_api/test_value_mapping.py` | High vs low support: infer UDF/axiom/lemma parameters from a highlight; engine tests plus HTTP. |
| `equational_reasoning_api/test_rewrite_logic.py` | Engine-only `rewrite logic` (`AdvLogic`) equivalences and rejections. |
| `equational_reasoning_api/test_hidden_expression.py` | Hidden definition bodies: model/serializer, helpers, student validation, masking on get-proof-lines. |
| `equational_reasoning_api/test_rule_comparison.py` | `normalize_rule_string` / `compare_rule` for hidden-field checks (`with`, `↦` vs `=`, high-support bare `apply F`). |

---

## Django app: `induction_api/`

| File | What it tests |
|---|---|
| `induction_api/tests.py` | Create/start/clear proofs, list (some list cases skipped), engine endpoints (`set-current-proof`, `apply-rule`, `check-goal`, `delete-line`, substitution), URL registration. |
| `induction_api/test_check_complete.py` | `TwoSidedProof.checkComplete()` ignores trailing blank (cleared) lines. |
| `induction_api/test_set_parameters.py` | Induction support-parameter fields and `PATCH /set-parameters`. |
| `induction_api/test_proof_management.py` | Clear / archive / restore induction proofs. |
| `induction_api/test_proof_line_persistence.py` | Proof lines persist with the expected rules after API use. |
| `induction_api/test_database_persistence.py` | Broader line persistence, including rules written to the DB. |
| `induction_api/test_error_persistence.py` | Failed-rule errors stay on the correct case×side row (base vs leap isolation). |
| `induction_api/tests_is_complete_persistence.py` | `is_complete` defaults false, becomes true only when base **and** leap are done, and reverts on edit. |
| `induction_api/tests_name_conflict.py` | Cross-mode name uniqueness (induction vs equational), check-name-conflict endpoint, archive-on-reuse. |
| `induction_api/tests_proof_card_fields.py` | List endpoint includes leap goals and `is_complete` for proof cards. |
| `induction_api/test_value_mapping_rule_response.py` | High support: apply-rule JSON `rule` includes `↦` mappings; low support does not. |
| `induction_api/test_wrong_highlight.py` | Engine-only: highlighting the wrong node on a UDF apply returns a user error instead of `IndexError`. |
| `induction_api/test_lemma_param_generics.py` | Engine-only: lemma free vars are not dropped because they match the caller’s generic names. |

---

## Django app: `assignments/`

| File | What it tests |
|---|---|
| `assignments/tests/tests_assignment_api.py` | Instructors cannot create assignments on another instructor’s course; deleting an assignment cascades. |
| `assignments/tests/tests_course_api.py` | Course term updates, invalid terms, instructor vs student list views, regenerating join codes. |
| `assignments/tests/tests_invitation_api.py` | Students can accept or reject course invitations. |
| `assignments/tests/tests_permissions.py` | Students cannot open inactive courses; instructors can. |
| `assignments/tests/tests_proof_cloning.py` | Starting an assignment proof deep-clones the template; restarting returns the existing clone. |
| `assignments/tests/tests_roster_api.py` | Join codes, instructor add/remove, duplicate-email conflict, leave-course, invitation cleanup. |

---

## Django app: `racket_api/`

| File | What it tests |
|---|---|
| `racket_api/tests.py` | Empty Django placeholder (`# Create your tests here.`). |
| `racket_api/test_delete_definition_cache.py` | After permanently deleting a UDF, the same label can be created again (engine cache is cleaned). Duplicate labels are still rejected while the definition exists. |

---

## Django app: `accounts/`

| File | What it tests |
|---|---|
| `accounts/tests.py` | Empty Django placeholder. Auth is not covered by an automated suite. |

---

## `expression_tree/` scripts (run with `python -m`, not `manage.py test`)

| File | What it tests |
|---|---|
| `expression_tree/runTests.py` | Orchestrator: `testApplyRule`, `testAdvMath`, then Django, then Jest. |
| `expression_tree/testApplyRule.py` | Import-time loop: `ERProof.addProofLine` for cons/first/rest/if/null?/zero? and related rules. Prints before/after or `errLog`. |
| `expression_tree/testAdvMath.py` | `rewrite math` helpers (`_fresh_var`, `_collect_node_names`, `_abstractedMathStr`) and `AdvMath.isApplicable`. |
| `expression_tree/test_rule_subclasses.py` | Broad `ERRuleset` Rule subclass coverage (built-in, math, logic, UDF, IH, lemma, axiom, AdvMath/AdvLogic, eval vs rewrite). |
| `expression_tree/test_rule_edge_cases.py` | Companion robustness cases and documented gaps (bad `startPos`, AdvMath false positives, shared rule-object mappings). |
| `expression_tree/testType.py.skip` / `.disabled` | Disabled type-system experiments. Not run. |
| `expression_tree/testDefinition.py.skip` / `.disabled` | Disabled definition experiments. Not run. |

---

## Standalone and non-app files

| File | How to run | What it tests |
|---|---|---|
| `django_server/test_manual_persistence.py` | `py manage.py test test_manual_persistence` | Django `TestCase`: creating `InductionProofLine` rows and reading them back. Not on the default all-apps path. |
| `test_equational_api.py` (repo root) | `py test_equational_api.py` with Django running | Live HTTP smoke of six equational endpoints. No auth headers; expect 401s unless you add a token. |
| `trial-automation.js` | `node trial-automation.js` (servers already up) | Puppeteer: log in, open induction, enable `(f n)`, fill a standard sum proof form. |
| `trial.ps1` | `.\trial.ps1` | Starts Django + React, then runs `trial-automation.js`. |

---

## Quick command cheat sheet

```powershell
# Windows: UTF-8 for Django output
$env:PYTHONIOENCODING = "utf-8"

# Almost everything
cd django_server
py -m expression_tree.runTests

# Django only
py manage.py test
py manage.py test induction_api --verbosity=2
py manage.py test equational_reasoning_api.test_value_mapping

# Expression engine only
py -m expression_tree.test_rule_subclasses
py -m expression_tree.test_rule_edge_cases

# Frontend only
cd ..\client
npm test
npm test -- --testPathPattern=playModeFeatures
```
