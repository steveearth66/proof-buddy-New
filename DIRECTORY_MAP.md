# Proof Buddy — Directory Map

This document explains every significant directory and file in the repository. It is intended to orient someone completely new to the project — human developer or AI assistant — so they can quickly locate any piece of logic.

---

## Top-level Files

| File | Purpose |
|---|---|
| `README.md` | Entry-point documentation for humans. Points to detailed setup guides in `documentation/`. |
| `docker-compose.yml` | Defines three Docker services: `django_server`, `nginx`, `client`. Wires together the full production stack. |
| `package.json` | Root-level npm configuration (not used for building; may be a workspace meta file). |
| `deploy.sh` | Shell script for deployment automation. |
| `start-dev.bat` / `start-dev.ps1` | Windows convenience scripts to launch both servers for local development. |
| `AInotes.txt` | **Critical developer notes.** Written by the primary developer to guide AI assistants. Contains workflow principles, architecture boundaries, recurring bug patterns, and session summaries. Any AI working on this project should read this file first. |
| `EquationalReasoningPlan.txt` | Step-by-step plan that was followed to build the equational reasoning module. Documents architectural decisions made and tracks completion status. |
| `EquationalReasoningStatus.txt` | Current status summary of the equational reasoning feature. |
| `LIST_INDUCTION_PROGRESS.md` | Tracks the in-progress work to support list induction (as distinct from integer induction). |
| `eqrnPlan.txt` | Earlier planning notes for equational reasoning. |
| `TESTING_GUIDE.md` | Instructions for running tests. |
| `test_equational_api.py` | Standalone integration test script for the equational reasoning API (runs outside Django test runner). |
| `trial.ps1` / `trial-automation.js` | Scripts for automated testing of proof workflows. |
| `make_proofbuddy_induction_ppt.py` | Utility to generate a PowerPoint presentation describing the induction proof system. (Research/presentation artifact.) |
| `hooks.json` | Git hooks configuration. |

---

## `client/` — React Frontend

The entire browser-side application. Built with React 18, bundled with Create React App / Babel, styled with Bootstrap 5 + SCSS.

### `client/src/`

**Entry points:**
- `index.js` — Mounts the React application into the DOM.
- `App.js` — Wraps the app in `AuthProvider` context and renders `AppRoutes`.
- `App.css` / `index.scss` — Global styles.

**`client/src/routes/`** — React Router route definitions
| File | Purpose |
|---|---|
| `index.js` | Root router using `HashRouter`. Composes Auth, Verification, and Proof sub-route groups. |
| `AuthRoutes.js` | Routes for `/login`, `/signup`, `/forgot-password`, etc. |
| `VerificationRoutes.js` | Routes for email verification and account activation flows. |
| `ProofRoutes.js` | Routes for all proof-mode pages (equational, induction, natural deduction). Protected — requires authentication. |

**`client/src/pages/`** — Top-level page components (one per URL path)
| File | Purpose |
|---|---|
| `Home.js` | Landing page. Shows available proof types. Routes the user to the selected editor. |
| `EquationalReasoningNew.js` | **Primary equational reasoning editor** (~400 lines). The clean, modernized version of the equational reasoning UI. Uses the `equational_reasoning_api` backend. |
| `EquationalReasoning.js` | Older equational reasoning page (preserved as fallback/reference). |
| `ERRacket.js` / `EquationalReasoningRacket.js` | Legacy equational editors backed by the old `racket_api`. Still functional. Do not modify without caution. |
| `InductionRacket.js` | **Mathematical induction editor** (~2400 lines). Handles both integer and list induction. Includes base/leap case switching, IH display, and full rule application UI. |
| `NaturalDeductionPropositionalLogic.js` | Legacy TFL/propositional logic page. |
| `NaturalDeductionFirstOrderLogic.js` | Legacy FOL page. |
| `Login.js` / `SignUp.js` / `ForgotPassword.js` | Authentication pages. |
| `PageNotFound.js` | 404 catch-all page. |

**`client/src/components/`** — Reusable React components
| File | Purpose |
|---|---|
| `PersistentPad.js` | **Core proof-line interaction component.** Renders a single proof line as syntax-highlighted text with clickable nodes. Supports arrow-key navigation up/down/left/right through the expression tree (using `jsonTree`) and stores node selections in `sessionStorage`. Exposes ref methods for the parent page to read the currently selected node ID and rule text. |
| `Definitions.jsx` | UI for managing user-defined functions (UDFs). Allows creating, editing, enabling/disabling, and deleting definitions. Default (built-in) UDFs displayed read-only. Persists to `sessionStorage`. |
| `Substitution.jsx` | Modal dialog for applying `eval` rules that require a substitution expression. User enters the expression to match and the rule to apply. |
| `ClickableRowNumber.js` | A row-number widget that can be clicked to bind a rule application to a specific proof line. |
| `RacketInput.jsx` | Input field with parenthesis-balanced highlighting for Racket expressions. |
| `ProofComplete.jsx` | Overlay with confetti animation triggered when `checkComplete` returns true. |
| `RuleSet.js` / `OffcanvasRuleSet.js` | Reference cards listing all available proof rules and their syntax. Displayed as a sidebar or offcanvas panel. |
| `Header.js` / `Footer.js` | Site-wide layout chrome. |

**`client/src/services/`** — API call wrappers (Axios-based)
| File | Purpose |
|---|---|
| `equationalService.js` | Wrappers for all `/api/v1/equational/...` endpoints. |
| `inductionService.js` | Wrappers for all `/api/v1/induction/...` endpoints. |
| `authService.js` | Wrappers for login, signup, logout, password reset. |
| `proofsService.js` | Wrappers for saving, loading, and deleting proofs. |

**`client/src/context/`** — React Context providers
- `AuthProvider`: Holds the current user's auth token and user info in React context. Consumed throughout the component tree to determine login state and user identity.

**`client/src/hooks/`** — Custom React hooks
- `useRacketRuleFields`: Manages the array of proof-line field state (racket expression, rule, start position, selected node, visibility flags, errors). Used by both `EquationalReasoningNew.js` and `InductionRacket.js` to keep proof-line UI state DRY.

**`client/src/config/`** — Configuration
- Contains the base URL for the backend API, read from the `REACT_APP_BACKEND_API_BASE_URL` environment variable at build time.

**`client/src/hoc/`** — Higher-order components
- Authentication guards; wrap proof routes to redirect unauthenticated users to `/login`.

**`client/src/utils/`** — Utility functions
- Shared helper functions used across pages and components.

**`client/src/scss/`** — SCSS stylesheets
- Component-level styles, custom Bootstrap overrides, color variables.

---

## `django_server/` — Python/Django Backend

### `django_server/django_server/` — Django project package
| File | Purpose |
|---|---|
| `settings.py` | Global configuration: database (MySQL), cache (db-based, 30-min timeout), installed apps, CORS allowed origins, DRF auth classes, email (SMTP). |
| `urls.py` | Root URL router. Mounts all Django app URL configurations under `/api/v1/`. |
| `asgi.py` / `wsgi.py` | ASGI/WSGI entry points for deployment. |

### `django_server/expression_tree/` — Proof Engine (core library)

This is the most intellectually significant directory in the project. It is a pure-Python library that implements all proof logic. It has no Django dependencies — it could be extracted and used independently.

| File | Purpose |
|---|---|
| `Parser.py` | **Tokenizer and AST builder.** `preProcess()` validates and tokenizes a Racket-like expression string. `buildTree()` recursively builds a `Node` tree from the token list. `makeBasicAst()` is the main public entry point combining both steps. |
| `ERCommon.py` | **Core data structures.** Defines `Node` (AST node), `RacType` (type representation), the `Type` enum, and tree utility functions including `findNode()` (locate a node by start position) and `makeJson()` (convert a tree to the JSON format sent to the frontend). |
| `ERobj.py` | **Built-in operator definitions.** Defines `ERobj` descriptors and a library of pre-built primitive operations: arithmetic (`+`, `-`, `*`, `expt`, `quotient`, `remainder`), comparisons (`=`, `>`, `<`), logic (`and`, `or`, `not`, `xor`, `implies`), list operations (`cons`, `first`, `rest`), type predicates (`null?`, `zero?`, `integer?`, `list?`), and `if`. |
| `expressionDefinition.py` | **Type labeler.** `labelTree()` walks a freshly-parsed Node tree and assigns types to all nodes by looking up built-ins and UDFs in lookup tables. This is a first pass before full type checking. |
| `Decorator.py` | **Type checker / propagator.** Walks the type-labeled tree and propagates type information through the tree, detecting type mismatches and recording errors. |
| `ERGenerics.py` | **Generic variable system.** Defines `GenericInt`, `GenericList`, `GenericBool`, `GenericAny`. Generics represent unspecified variables with typed constraints (e.g., "a non-negative integer"). Used in proof contexts where variables haven't been given concrete values. |
| `ERRuleset.py` | **All proof rules.** Defines an abstract `Rule` class and all concrete rule types: `BuiltIn`, `Math` (with SymPy), `Axiom`, `UDF`, `IH`, `If`. Each rule implements `isApplicable()` (can this rule be applied here?) and `insertSubstitution()` (what is the result?). The `isMatch()` helper checks structural tree equality. |
| `ERProofEngine.py` | **Proof session management.** Defines `ERProofLine` (one step), `ERProof` (one side of a proof), `TwoSidedProof` (equational reasoning proof), and `ProofComponent` (shared base class). `addProofLine()` is the main entry point for rule application. `checkComplete()` verifies LHS and RHS convergence. |
| `IndProofs.py` | **Induction proof structure.** Defines `IndProof`, which wraps two `TwoSidedProof` objects (one for the base case, one for the leap step) and adds metadata for the induction variable, anchor value, leap variable, and inductive hypothesis. |
| `Labeler.py` | Helper for expression labeling. |
| `default_udfs.py` | **Pre-built user-defined functions.** Provides `length`, `append`, and `countTruthTableRows` as built-in starter definitions available to all users. These are not stored in the database (they have negative `id` values). |
| `sluff.py` | Utility functions for tree manipulation. |
| `runTests.py` / `testAdvMath.py` / `testApplyRule.py` | Unit test files for the expression engine. |

### `django_server/equational_reasoning_api/` — Equational Reasoning Django App

| File | Purpose |
|---|---|
| `models.py` | `EquationalProof` (proof metadata) and `EquationalProofLine` (individual proof steps). See database schema section below. |
| `views.py` | **All equational reasoning API endpoints.** Six views: `set_current_proof`, `apply_rule`, `substitution`, `delete_line`, `check_completion`, `get_proof_lines`. Each view reconstructs the proof from cache/DB, calls the proof engine, saves results, and returns JSON. |
| `serializers.py` | DRF serializers for `EquationalProof`. Validates that LHS and RHS goals are non-empty and not identical. |
| `urls.py` | URL patterns for all equational endpoints, mounted at `/api/v1/equational/`. |
| `tests.py` | 11 automated tests for models, serializers, and proof behavior. |
| `test_integration.py` | Additional integration tests. |

### `django_server/induction_api/` — Induction Django App

| File | Purpose |
|---|---|
| `models.py` | `InductionProof` and `InductionProofLine`. Similar to equational models but includes `case` (base/leap), `proof_type` (int/list), IH fields, and induction variable metadata. |
| `views.py` | Endpoints: `start_induction_proof`, `apply_rule`, `substitution`, `delete_line`, `check_goal`, `get_proof_lines`, and others. Same overall pattern as equational but includes `case` context throughout. |
| `urls.py` | URL patterns mounted at `/api/v1/induction/`. |
| `README.md` | Internal documentation for the induction API. |

### `django_server/accounts/` — User Authentication App

| File | Purpose |
|---|---|
| `models.py` | `Account` (custom user model extending `AbstractBaseUser`): email, username, first/last name, `is_instructor` flag, `is_active`. Also `ActivateAccount` for email verification tokens. |
| `views.py` | Login, signup, token creation, password reset, email verification, username lookup. |
| `urls.py` | Auth URL patterns mounted at `/api/v1/auth/`. |
| `serializers.py` | Serializers for account creation and retrieval. |

### `django_server/proofs/` — Legacy Proof Storage App

| File | Purpose |
|---|---|
| `models.py` | `Definition`, `Generic`, `Proof`, `ProofLine`. Original data models from before the equational/induction split. `Proof` supports multiple "templates" (ER, MP, MT, DS, ADD). |
| `views.py` | CRUD for definitions, generics, and legacy proofs. |
| `urls.py` | URL patterns mounted at `/api/v1/proofs`. |

### `django_server/racket_api/` — Legacy Proof Validation App

Provides the backend for the legacy `ERRacket.js` frontend. Contains proof validation logic that predates the current `expression_tree` architecture. Should not be modified.

### `django_server/assignments/` — Assignment Management App

| File | Purpose |
|---|---|
| `models.py` | `Course` (course section), `Assignment` (problem set with due date), `Course` has an instructor and a set of student `Account` references. |
| `views.py` | Instructor CRUD for terms and assignments; student submission endpoints. |

---

## `database/` — Database Setup Scripts

| File | Purpose |
|---|---|
| `docker-compose.yml` | Docker Compose configuration for running just the MySQL database in a container (useful for development without a full local MySQL install). |
| `setup.sql` | Initial SQL script to create the database and user. |

---

## `nginx/` — Reverse Proxy Configuration

| File | Purpose |
|---|---|
| `nginx.conf` | Nginx configuration. Defines an `upstream` pointing to `django_server:8000`. Routes all requests under `/` to Django and serves `/static/` files from a shared Docker volume. |

---

## `documentation/` — Project Documentation

| Directory | Purpose |
|---|---|
| `docker/` | Docker setup guides. |
| `readme_resources/` | Detailed local installation guides: first-time setup, `.env` file creation, running the application, API reference. |
| `use_cases/` | Use case diagrams or descriptions of user workflows. |
| `user_documentation/` | End-user and developer documentation including the API reference. |

---

## `django_server/` Root-Level Files

| File | Purpose |
|---|---|
| `manage.py` | Django management command entry point. |
| `requirements.txt` | Python package dependencies. |
| `Dockerfile` | Docker image definition for the Django server. |
| `entrypoint.sh` | Docker container startup script (runs migrations, collectstatic, starts Gunicorn). |
| `gunicorn.conf.py` | Gunicorn WSGI server configuration (workers, bind address). |
| `test_manual_persistence.py` | Developer script for manually testing proof persistence behavior. |
