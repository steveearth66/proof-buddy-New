# Proof Buddy — API Reference (Testing Edition)

Complete HTTP API reference for writing contract tests, integration tests, and manual API checks. Documents **as-implemented** behavior from Django views and `urls.py`.

**Status:** De-facto / exploratory. No OpenAPI spec. Lock envelope **keys** in tests; do not lock exact error **strings** until team decides.

### Related documentation


| Document                                                                                                      | Role                                                                                                               |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| [API_REFERENCE.md](API_REFERENCE.md)                                                                          | **This file** — HTTP API reference: routes, params, and responses                                                  |
| [DATA_FLOW.md](../DATA_FLOW.md)                                                                               | What happens inside Django after each API call (engine, cache, DB)                                                 |
| [ARCHITECTURE.md](../ARCHITECTURE.md)                                                                         | System overview: frontend, backend apps, auth, deployment                                                          |
| [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)                                                                   | Proof engine internals, where to change rules, how to extend the system                                            |
| [TESTING_GUIDE.md](../TESTING_GUIDE.md)                                                                       | How to run backend and frontend tests                                                                              |
| [COURSE_APIS.md](user_documentation/Courses/COURSE_APIS.md)                                                   | Assignments/courses narrative spec with sample JSON (some paths differ from code; prefer this file for routes)     |
| [induction_api/README.md](../django_server/induction_api/README.md)                                           | Induction endpoint walkthrough with curl examples                                                                  |
| [4_API_reference.md](user_documentation/local_installation/documentation/readme_resources/4_API_reference.md) | **Legacy** — minimal auth-only list; outdated paths (`register`, `/users/profile`); kept for old install-doc links |


---



## Table of contents

1. [Global conventions](#global-conventions)
2. [Auth —](#auth) `/api/v1/auth/`
3. [Equational —](#equational) `/api/v1/equational/`
4. [Induction —](#induction) `/api/v1/induction/`
5. [Legacy proof —](#legacy-proof) `/api/v1/proof/`
6. [Proofs —](#proofs) `/api/v1/proofs`
7. [Assignments —](#assignments) `/api/v1/assignments/`
8. [Known issues](#known-issues)

---



## Global conventions


| Topic         | Detail                                                                                                                                    |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Base URL      | `/api/v1/`                                                                                                                                |
| Format        | JSON request/response                                                                                                                     |
| Auth header   | `Authorization: Token <accessToken>`                                                                                                      |
| Token source  | `POST /api/v1/auth/signin` → `{ accessToken, username }`                                                                                  |
| Session cache | Equational: `equational_obj_{username}`. Induction: `induction_obj_{username}`, `induction_proof_{username}`. Legacy: `proofs_{username}` |
| Call order    | Initialize session before rule application                                                                                                |
| Soft fail     | Many proof endpoints return **200** + `"isValid": false`                                                                                  |
| Persistence   | `get-proof-lines` may return `{ "hasProof": false }` until proof is saved/loaded                                                          |




### Canonical vs legacy


| Prefix                 | Status            | Client service                     |
| ---------------------- | ----------------- | ---------------------------------- |
| `/api/v1/equational/`  | **Canonical**     | `equationalService.js`             |
| `/api/v1/induction/`   | **Canonical**     | `inductionService.js`              |
| `/api/v1/proof/`       | **Legacy**        | `erService.js`                     |
| `/api/v1/proofs`       | Sparse (2 routes) | `proofsService.js`                 |
| `/api/v1/auth/`        | Canonical         | `authService.js`, `userService.js` |
| `/api/v1/assignments/` | Canonical         | `courseServices.js`                |


---



## Auth

**Prefix:** `/api/v1/auth/` · **App:** `accounts/` · **Cache:** none

### `POST /api/v1/auth/signup`


| Field       | Detail                                                                                       |
| ----------- | -------------------------------------------------------------------------------------------- |
| Auth        | No                                                                                           |
| Body        | `email` (string), `username` (string), `password` (string), `is_instructor` (bool, optional) |
| Success 201 | `{ "message": "Account created!" }`                                                          |
| Fail 400    | `{ "message": { "<field>": ["..."] } }`                                                      |




### `POST /api/v1/auth/signin`


| Field       | Detail                                                         |
| ----------- | -------------------------------------------------------------- |
| Auth        | No                                                             |
| Body        | `username` (string), `password` (string)                       |
| Success 200 | `{ "accessToken": string, "username": string }`                |
| Fail 404    | Unknown username: `{ "message": "Invalid username/password" }` |
| Fail 400    | Wrong password: `{ "message": "Invalid username/password" }`   |




### `GET /api/v1/auth/profile`


| Field       | Detail                                                                       |
| ----------- | ---------------------------------------------------------------------------- |
| Auth        | **Yes**                                                                      |
| Success 200 | `{ "username", "email", "is_student" }` — `is_student` = `not is_instructor` |
| Fail 404    | `{ "message": "User not found" }`                                            |




### `POST /api/v1/auth/logout`


| Field       | Detail                                                                |
| ----------- | --------------------------------------------------------------------- |
| Auth        | Yes (token to invalidate)                                             |
| Body        | *(none)*                                                              |
| Success 200 | `{ "message": "Logged out" }` — always 200 even if token delete fails |




### `POST /api/v1/auth/activate-account`


| Field       | Detail                                    |
| ----------- | ----------------------------------------- |
| Auth        | No                                        |
| Body        | `activation_key` (string)                 |
| Success 200 | `{ "message": "Account activated" }`      |
| Fail 404    | `{ "message": "Invalid activation key" }` |




### `POST /api/v1/auth/forgot-password`


| Field       | Detail                            |
| ----------- | --------------------------------- |
| Auth        | No                                |
| Body        | `email` (string)                  |
| Success 200 | `{ "message": "Email sent" }`     |
| Fail 404    | `{ "message": "User not found" }` |




### `POST /api/v1/auth/reset-password`


| Field       | Detail                                    |
| ----------- | ----------------------------------------- |
| Auth        | No                                        |
| Body        | `reset_key` (string), `password` (string) |
| Success 200 | `{ "message": "Password reset" }`         |
| Fail 404    | `{ "message": "Invalid activation key" }` |




### `POST /api/v1/auth/resend-activation-email`


| Field       | Detail                            |
| ----------- | --------------------------------- |
| Auth        | No                                |
| Body        | `email` (string)                  |
| Success 200 | `{ "message": "Email sent" }`     |
| Fail 404    | `{ "message": "User not found" }` |


---



## Equational

**Prefix:** `/api/v1/equational/` · **App:** `equational_reasoning_api/` · **Cache key:** `equational_obj_{username}`

**Recommended call order:** `save-proof` or `upload-proof` or `get-user-proof` → `set-current-proof` → `apply-rule`/`substitution` → `get-proof-lines` → `check-completion`

### `POST /api/v1/equational/set-current-proof`


| Field           | Detail                                                                                                                                  |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Auth            | Yes                                                                                                                                     |
| Body            | `lhsPremise` (string, required), `rhsPremise` (string, required), `definitions` (array, default `[]`), `generics` (array, default `[]`) |
| Definition item | `{ label, type, expression, is_default?, deletable? }`                                                                                  |
| Generic item    | `{ label, type, restrictions }`                                                                                                         |
| Success 200     | `{ isValid: true, lhsPremise, rhsPremise, lhsJsonTree, rhsJsonTree }`                                                                   |
| Fail 400        | `{ isValid: false, errors: [...] }`                                                                                                     |


**Notes:** Does not create DB proof. Preserves `proof_id` from cache if present. Hard-fail uses 400 (not soft 200).

### `POST /api/v1/equational/apply-rule`


| Field         | Detail                                                                                                                                                                                                                            |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Auth          | Yes                                                                                                                                                                                                                               |
| Body          | `side` (string, default `"LHS"`), `currentRacket` (string), `rule` (string), `startPosition` (int, default 0), `selectedNode` (int), `substitution` (string), `lineNumber` (int), `supportRewriteComplexity` (bool, default true) |
| Success 200   | `{ isValid, racket, jsonTree, rule, resultNodeId, errors }`                                                                                                                                                                       |
| Soft-fail 200 | `isValid: false`, `racket: "Error generating racket"`, `jsonTree: {}`                                                                                                                                                             |
| Fail 400      | `{ isValid: false, errors: [...] }`                                                                                                                                                                                               |


**Notes:** Reloads lines from DB. Soft-fail on hidden/unimplemented definitions and misuse of `rewrite math`/`rewrite logic` in rule field.

### `POST /api/v1/equational/substitution`

Same body/response as `apply-rule`. Maps `rule: "math"` → `"rewrite math"`, `"logic"` → `"rewrite logic"`. Does not reload DB lines before acting.

### `DELETE /api/v1/equational/delete-line/<side>/<line_number>`


| Field       | Detail                                                    |
| ----------- | --------------------------------------------------------- |
| Auth        | Yes                                                       |
| URL         | `side` (`LHS`/`RHS`), `line_number` (int)                 |
| Success 200 | `{ success: true, message: "Line cleared successfully" }` |
| Fail 400    | `{ success: false, error: "..." }`                        |


**Notes:** Only clears when `line_number > 0`.

### `POST /api/v1/equational/check-completion`


| Field       | Detail                                                                  |
| ----------- | ----------------------------------------------------------------------- |
| Auth        | Yes                                                                     |
| Body        | *(empty)*                                                               |
| Success 200 | `{ isComplete: bool, message: "Proof complete!" | "Proof incomplete" }` |
| Fail 400    | `{ error: "..." }`                                                      |




### `GET /api/v1/equational/get-proof-lines`


| Field            | Detail                                                                                                                                                |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Auth             | Yes                                                                                                                                                   |
| No proof_id 200  | `{ hasProof: false }`                                                                                                                                 |
| Unauthorized 403 | `{ hasProof: false }`                                                                                                                                 |
| Success 200      | `{ hasProof: true, user, lhsAnchorGoal, rhsAnchorGoal, proofName, tag, proof_id, support_*, visible_rules, LHS[], RHS[], definitions[], generics[] }` |


**Line object:** `lineNumber`, `racket`, `rule`, `jsonTree`, `selectedNode`, `resultNode`, `substitution`, `startPosition`, `hide_expression`, `hide_justification`, `errors`

### `POST /api/v1/equational/toggle-visibility`


| Field       | Detail                                                                                             |
| ----------- | -------------------------------------------------------------------------------------------------- |
| Body        | `side` (required), `lineNumber` (required), `field` (required: `"expression"` | `"justification"`) |
| Success 200 | `{ success: true, line_number, side, field, new_value }`                                           |
| Fail 400    | `{ error: "..." }` — requires `proof_id` in cache                                                  |




### `POST /api/v1/equational/toggle-visibility-premise`

Same as toggle-visibility plus optional `setting_visibility` (bool) to set instead of toggle.

### `POST /api/v1/equational/validate-hidden-field`


| Field        | Detail                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------- |
| Body         | `side`, `lineNumber` (required); `studentRule`, `studentExpression`, `studentSelectedNode` (optional) |
| Success 200  | `{ isValid, errors, hide_expression, hide_justification, message }`                                   |
| Fail 400/404 | `{ error: "..." }`                                                                                    |




### `POST /api/v1/equational/validate-hidden-definition`


| Field        | Detail                                                           |
| ------------ | ---------------------------------------------------------------- |
| Body         | `label` (required), `student_expression` (required)              |
| Success 200  | `{ isValid: true, expression }` or `{ isValid: false, message }` |
| Fail 400/500 | `{ error: "..." }`                                               |




### `GET /api/v1/equational/proofs`


| Field       | Detail                                                        |
| ----------- | ------------------------------------------------------------- |
| Query       | `page` (default 1), `query` (name filter)                     |
| Success 200 | `{ proofs[], totalPages, currentPage, hasNext, hasPrevious }` |


**Proof item:** `id`, `name`, `tag`, `lhs`, `rhs`, `isComplete`, `proofLines[]`, `definitions[]`

### `POST /api/v1/equational/get-user-proof`


| Field        | Detail                                                       |
| ------------ | ------------------------------------------------------------ |
| Body         | `proof_id` (int, required)                                   |
| Success 200  | `{ success: true, message: "Proof loaded and DB repaired" }` |
| Fail 400/404 | `{ error: "..." }`                                           |


**Notes:** Loads into cache; call `get-proof-lines` after for data.

### `POST /api/v1/equational/clear-proof`


| Field       | Detail                                        |
| ----------- | --------------------------------------------- |
| Body        | *(empty)*                                     |
| Success 200 | `{ message: "Session cleared successfully" }` |


**Notes:** Cache only; DB proof unchanged.

### `POST /api/v1/equational/discard-proof`


| Field       | Detail                                       |
| ----------- | -------------------------------------------- |
| Success 200 | `{ message: "Proof archived successfully" }` |


**Notes:** Archives most recent active proof (`is_active=false`), clears cache.

### `POST /api/v1/equational/save-proof`


| Field       | Detail                                                                                                                                                                     |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Body        | `name` (required), `tag`, `lHSGoal`, `rHSGoal` (required), `leftPremise`, `rightPremise`, `leftRacketsAndRules[]`, `rightRacketsAndRules[]`, `definitions[]`, `generics[]` |
| Line object | `racket`, `rule`, `startPosition`, `substitution`, `selectedNode`, `resultNode`, `errors`, `jsonTree`                                                                      |
| Success 201 | `{ message: "Proof saved successfully", proofId }`                                                                                                                         |
| Fail 400    | `{ message: "Error saving proof" }`                                                                                                                                        |


**Notes:** Reserved names rejected: `IH`, `length`, `append`, `reverse`. Does not update cache.

### `POST /api/v1/equational/delete-proof`


| Field       | Detail                                     |
| ----------- | ------------------------------------------ |
| Body        | `proof_id` (int, required)                 |
| Success 200 | `{ success: true, message, cacheCleared }` |
| Fail 404    | `{ error: "Proof not found" }`             |




### `PATCH /api/v1/equational/set-parameters`


| Field        | Detail                                                                                                                                                                                                    |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Auth         | **Instructor only** (proof must belong to user)                                                                                                                                                           |
| Body         | `proof_id` (required); optional: `support_errors`, `support_current_lhs_rhs`, `support_ih`, `support_premise`, `support_rule_set`, `support_value_mapping`, `visible_rules`, `support_rewrite_complexity` |
| Success 200  | All 8 param fields with current values                                                                                                                                                                    |
| Fail 403/404 | `{ error: "..." }`                                                                                                                                                                                        |




### `GET /api/v1/equational/download-proof`


| Field       | Detail                                                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Query       | `proof_id` (required)                                                                                                                  |
| Success 200 | Export JSON: `proofType: "equational"`, `name`, `tag`, `lhsGoal`, `rhsGoal`, `definition[]`, `support_*`, `lines.LHS[]`, `lines.RHS[]` |




### `POST /api/v1/equational/upload-proof`


| Field       | Detail                                                              |
| ----------- | ------------------------------------------------------------------- |
| Body        | Same shape as download response; `proofType` must be `"equational"` |
| Success 201 | `{ proofId, proofName }`                                            |
| Fail 400    | `{ error: "..." }`                                                  |




### `POST /api/v1/equational/save-comment`


| Field       | Detail                                                                  |
| ----------- | ----------------------------------------------------------------------- |
| Body        | `side`, `line_number`, `role` (`"student"` | `"instructor"`), `comment` |
| Success 200 | `{ success: true }`                                                     |




### `GET /api/v1/equational/get-comments`


| Field       | Detail                            |
| ----------- | --------------------------------- |
| Query       | `side`, `line_number` (required)  |
| Success 200 | `{ student: "", instructor: "" }` |




### `GET /api/v1/equational/get-comment-status`


| Field       | Detail                                          |
| ----------- | ----------------------------------------------- |
| Success 200 | `{}` or `{ "LHS-0": true, "RHS-2": true, ... }` |


---



## Induction

**Prefix:** `/api/v1/induction/` · **App:** `induction_api/` · **Cache:** `induction_obj_{username}`, `induction_proof_{username}`

**Recommended call order:** `start-induction-proof` → `set-current-proof` → `apply-rule`/`substitution` → `check-completion`

**Resume:** `POST set-induction-session-by-id` with `{ proof_id }` → editing endpoints.

### `POST /api/v1/induction/start-induction-proof`


| Field        | Detail                                                                                                                                                                                                                                                                                                                                                    |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Body         | `proof_name` (required), `induction_variable` (required), `anchor_value` (required), `leap_variable` (required); optional: `proof_tag`, `side`, `lhs_leap_goal`, `rhs_leap_goal`, `lhs_anchor_goal`, `rhs_anchor_goal`, `induction_type` (`"integers"` | `"lists"`), `is_anchor`, `inductive_hypothesis_lhs`, `inductive_hypothesis_rhs`, `definitions[]` |
| Success 201  | `{ message, proof_id, proof_name, proof_tag, generic_definition_created, generics_created, data, inductive_hypothesis_lhs, inductive_hypothesis_rhs }`                                                                                                                                                                                                    |
| Fail 400/500 | Validation or internal error                                                                                                                                                                                                                                                                                                                              |


**Notes:** Archives existing active proof with same name. Call `set-current-proof` next.

### `POST /api/v1/induction/clear-induction`


| Field       | Detail                     |
| ----------- | -------------------------- |
| Body        | *(none)*                   |
| Success 200 | `{ message, proof_name? }` |


**Notes:** Soft-deletes active proof, clears `induction_obj_` cache.

### `POST /api/v1/induction/new-proof`


| Field       | Detail                                        |
| ----------- | --------------------------------------------- |
| Auth        | Yes                                           |
| Success 200 | `{ message: "Session cleared successfully" }` |


**Notes:** Clears cache only; DB proof remains.

### `POST /api/v1/induction/create-induction-proof/`


| Field       | Detail                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| Body        | `induction_variable`, `anchor_value`, `leap_variable`, `lhs_expression`, `rhs_expression` (all required) |
| Success 201 | Full `InductionProof` serializer object                                                                  |
| Fail 400    | `{ error, details }`                                                                                     |


**Notes:** Legacy simpler create; no `proof_name`.

### `GET /api/v1/induction/get-induction-proofs/`


| Field       | Detail                              |
| ----------- | ----------------------------------- |
| Query       | `query` (name filter, optional)     |
| Success 200 | `{ proofs: [InductionProof, ...] }` |




### `GET /api/v1/induction/proof/<proof_id>/`


| Field       | Detail                         |
| ----------- | ------------------------------ |
| Success 200 | Full `InductionProof` object   |
| Fail 403    | `{ hasProof: false }`          |
| Fail 404    | `{ error: "Proof not found" }` |




### `POST /api/v1/induction/set-current-proof`


| Field       | Detail                                                                                                                   |
| ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| Body        | `struct` (default `"int"`), `ivar`, `aval`, `lvar`, `lhsPremise`, `rhsPremise` (required); `definitions[]`, `generics[]` |
| Success 201 | `{ isValid: true, errors: [], base: { LHS, RHS }, leap: { LHS, RHS } }` — each side has `racket`, `jsonTree`             |
| Fail 400    | `{ isValid: false, errors: [...] }`                                                                                      |




### `POST /api/v1/induction/apply-rule`


| Field       | Detail                                                                                                                                                                                                |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Auth        | Yes                                                                                                                                                                                                   |
| Body        | `case` (default `"base"` — also `anchor`, `leap`, etc.), `side` (default `"LHS"`), `currentRacket`, `rule`, `startPosition`, `selectedNode`, `substitution`, `lineNumber`, `supportRewriteComplexity` |
| Success 200 | `{ isValid, racket, errors, jsonTree, lineNum, resultNodeId, rule }`                                                                                                                                  |
| Fail 400    | `{ isValid: false, errors: [...] }`                                                                                                                                                                   |




### `DELETE /api/v1/induction/delete-line/<case>/<side>/<line_number>`


| Field       | Detail             |
| ----------- | ------------------ |
| Success 200 | Empty body         |
| Fail 500    | `{ error: "..." }` |


**Notes:** Clears line (does not remove row). Only when `line_number > 0`.

### `POST /api/v1/induction/check-goal`


| Field       | Detail                                                                 |
| ----------- | ---------------------------------------------------------------------- |
| Body        | `case` (default `"base"`), `side` (default `"LHS"`), `goal` (required) |
| Success 200 | `{ isValid, errors, jsonTree }`                                        |


**Notes:** Uses fresh engine; does not persist. Used to validate goals before start.

### `POST /api/v1/induction/substitution`

Same body pattern as apply-rule. Maps `math`/`logic` to rewrite rules.

### `POST /api/v1/induction/check-completion`


| Field       | Detail                            |
| ----------- | --------------------------------- |
| Body        | `case` (default `"base"`)         |
| Success 200 | `{ isComplete, label: "BASE CASE" |


**Notes:** `overallComplete` requires both cases complete and no hidden fields (students).

### `GET /api/v1/induction/get-proof-lines`


| Field       | Detail                                               |
| ----------- | ---------------------------------------------------- |
| Success 200 | `{ base: { LHS[], RHS[] }, leap: { LHS[], RHS[] } }` |


**Line keys:** `racket`, `rule`, `startPosition`, `selectedNode`, `resultNode`, `lineNumber`, `substitution`, `jsonTree`, `errors`, `hide_expression`, `hide_justification`

### `GET /api/v1/induction/get-current-proof`


| Field          | Detail                                                                                                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| No session 200 | `{ hasProof: false }`                                                                                                                                                                                                                      |
| Success 200    | `{ hasProof: true, inductionVariable, anchorValue, leapVariable, lhsAnchorGoal, rhsAnchorGoal, lhsLeapGoal, rhsLeapGoal, inductiveHypothesisLHS, inductiveHypothesisRHS, currentSide, isAnchorCase, proofName, tag, proof_id, support_* }` |




### `DELETE /api/v1/induction/clear-all-proof-lines`


| Field       | Detail                        |
| ----------- | ----------------------------- |
| Success 200 | `{ message, deleted_count? }` |




### `POST /api/v1/induction/set-induction-session-by-id`


| Field       | Detail                |
| ----------- | --------------------- |
| Auth        | Yes                   |
| Body        | `proof_id` (required) |
| Success 200 | `{ success: true }`   |
| Fail 403    | `{ hasProof: false }` |




### `POST /api/v1/induction/delete-proof`


| Field       | Detail                                     |
| ----------- | ------------------------------------------ |
| Auth        | Yes                                        |
| Body        | `proof_id` (required)                      |
| Success 200 | `{ success: true, message, cacheCleared }` |




### `GET /api/v1/induction/check-name-conflict`


| Field       | Detail                               |
| ----------- | ------------------------------------ |
| Auth        | Yes                                  |
| Query       | `name` (optional)                    |
| Success 200 | `{ conflict: bool, type: "Induction" |




### `PATCH /api/v1/induction/set-parameters`

Same shape as equational `set-parameters` (instructor only, `proof_id` required).

### `GET /api/v1/induction/download-proof`


| Field       | Detail                                                                             |
| ----------- | ---------------------------------------------------------------------------------- |
| Query       | `proof_id` (required)                                                              |
| Success 200 | Export with `proofType: "induction"`, goals, IH fields, `lines.base`, `lines.leap` |




### `POST /api/v1/induction/upload-proof`


| Field       | Detail                                                   |
| ----------- | -------------------------------------------------------- |
| Body        | Download export shape; `proofType` must be `"induction"` |
| Success 201 | `{ proofId, proofName }`                                 |




### `POST /api/v1/induction/validate-hidden-field`


| Field       | Detail                                                                                             |
| ----------- | -------------------------------------------------------------------------------------------------- |
| Body        | `side`, `case`, `lineNumber` (required); `studentExpression`, `studentRule`, `studentSelectedNode` |
| Success 200 | `{ isValid, errors, hide_expression, hide_justification, message }`                                |




### `POST /api/v1/induction/validate-hidden-definition`


| Field       | Detail                                                      |
| ----------- | ----------------------------------------------------------- |
| Body        | `label`, `student_expression` (required)                    |
| Success 200 | `{ isValid, expression? }` or `{ isValid: false, message }` |




### `POST /api/v1/induction/toggle-visibility`


| Field       | Detail                                               |
| ----------- | ---------------------------------------------------- |
| Body        | `side`, `lineNumber`, `field`, `case` (all required) |
| Success 200 | `{ success, line_number, side, field, new_value }`   |




### `POST /api/v1/induction/toggle-visibility-premise`

Same plus optional `setting_visibility` (bool).

### Comment endpoints


| Endpoint             | Method | Params/body                              | Response                         |
| -------------------- | ------ | ---------------------------------------- | -------------------------------- |
| `save-comment`       | POST   | `side`, `line_number`, `role`, `comment` | `{ success: true, created? }`    |
| `get-comments`       | GET    | query: `side`, `line_number`             | `{ student, instructor }`        |
| `get-comment-status` | GET    | —                                        | `{}` or `{ "LHS-0": true, ... }` |


---



## Legacy proof

**Prefix:** `/api/v1/proof/` · **App:** `racket_api/` · **Cache:** `proofs_{username}`

Modern equivalents exist under `/equational/`. Still used for definitions/generics via `erService.js`.


| Method | Path                         | Body / params                                                                                                                                                  | Response keys                                                | Notes                      |
| ------ | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------- |
| POST   | `set-proof`                  | `definitions[]`, `generics[]`, `leftGoalChecked`, `lHSGoal`, `rightGoalChecked`, `rHSGoal`, `LHS[]`, `RHS[]` (lines: `currentRacket`, `rule`, `startPosition`) | 201: `{ isValid: "True", errors: [] }` — **string** `"True"` | Call first to init cache   |
| POST   | `er-generate`                | `side`, `currentRacket`, `rule`, `startPosition`                                                                                                               | `{ isValid, racket, errors, jsonTree, lineNum }`             | Soft-fail 200              |
| POST   | `er-substitution`            | + `substitution`                                                                                                                                               | Same as er-generate                                          |                            |
| POST   | `check-goal`                 | `name`, `tag`, `side`, `goal`, `loadedProofId?`                                                                                                                | `{ isValid, errors, jsonTree }`                              | Soft-fail on name conflict |
| DELETE | `delete-line/<side>`         | URL: `side`                                                                                                                                                    | Empty 200                                                    |                            |
| POST   | `er-clear`                   | —                                                                                                                                                              | Empty 200                                                    | Clears cache               |
| POST   | `er-save`                    | See save body below                                                                                                                                            | `{ message }` 201                                            | Persists to DB             |
| POST   | `er-complete`                | Same as er-save                                                                                                                                                | Empty 200                                                    | Sets `isComplete`          |
| GET    | `proofs`                     | query: `page`, `query`                                                                                                                                         | `{ proofs, totalPages, currentPage, hasNext, hasPrevious }`  |                            |
| GET    | `proofs/<proof_id>`          | URL: `proof_id`                                                                                                                                                | Full loaded proof object                                     | Loads into cache           |
| POST   | `er-definitions`             | `label`, `type`, `expression`, `notes`, `expression_hidden?`                                                                                                   | Definition object 201                                        |                            |
| GET    | `get-definitions`            | —                                                                                                                                                              | Array of definitions                                         |                            |
| GET    | `use-definition/<label>`     | URL: `label`                                                                                                                                                   | `{ message }`                                                | **GET not POST**           |
| POST   | `edit-definition/`           | `label`, `type`, `expression`, `notes`, `expression_hidden?`                                                                                                   | Updated definition                                           | Trailing slash             |
| DELETE | `delete-definition/<label>/` | URL: `label`                                                                                                                                                   | Empty 200                                                    | DB + cache                 |
| DELETE | `remove-definition/<label>/` | URL: `label`                                                                                                                                                   | Empty 200                                                    | Cache only                 |
| GET    | `get-generics`               | —                                                                                                                                                              | Array with `enabled`                                         |                            |
| POST   | `create-generic`             | `label`, `type`, `restrictions?`, `notes?`                                                                                                                     | Generic object 201                                           |                            |
| GET    | `use-generic/<id>`           | URL: `id`                                                                                                                                                      | Empty or `{ message }`                                       |                            |
| DELETE | `remove-generic/<id>`        | URL: `id`                                                                                                                                                      | Empty 200                                                    | Disable in session         |
| DELETE | `delete-generic/<id>`        | URL: `id`                                                                                                                                                      | Empty 200                                                    | DB + session               |


**Save/complete body (**`er-save`**,** `er-complete`**):** `name`, `tag`, `lHSGoal`, `rHSGoal`, `leftPremise`, `rightPremise`, `leftRacketsAndRules[]`, `rightRacketsAndRules[]`, `definitions[]`, `generics` (dict keyed by label)

---



## Proofs

**Prefix:** `/api/v1/proofs` (no trailing slash)


| Method | Path                | Body                                                    | Response                                        | Notes                                                             |
| ------ | ------------------- | ------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------- |
| DELETE | `delete-proof/<id>` | URL: `id`                                               | `{ message: "Proof successfully deleted" }` 200 | **No auth check**                                                 |
| PUT    | `edit=proof/<id>`   | `name`, `tag`, `lhs`, `rhs`, `created_at`, `isComplete` | `{ message: "Proof successfully updated" }` 200 | **URL typo** `edit=proof`. Client calls `edit-proof`. **No auth** |


---



## Assignments

**Prefix:** `/api/v1/assignments/` · **App:** `assignments/` · **Auth:** All endpoints require token (401 without)

Full narrative spec also in [COURSE_APIS.md](user_documentation/Courses/COURSE_APIS.md) — **prefer paths below** where they differ.

### Courses


| Method | Path                  | Body / params                                                                                                  | Roles                              | Success                                                 |
| ------ | --------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------- |
| GET    | `courses`             | —                                                                                                              | Any                                | 200: course array (instructor vs student shape differs) |
| POST   | `courses`             | `name` (req), `students[]`, `generate_join_code`, `expiration_date`                                            | Instructor                         | 201 + optional `join_code`                              |
| GET    | `courses/<course_id>` | URL: `course_id`                                                                                               | Owner, enrolled student, superuser | 200: single course                                      |
| PATCH  | `courses/<course_id>` | `{ action: "regenerate_code" }` OR partial: `name`, `is_active`, `term`, `description`, `join_code_expires_at` | Owner, superuser                   | 200                                                     |


**Term validation:** `^(Spring|Summer|Fall|Winter) \d{4}$`

**403 messages:** `"You are not authorized to view/manage this course."`

### Assignments CRUD


| Method | Path                                 | Body                                                     | Roles                     | Success                       |
| ------ | ------------------------------------ | -------------------------------------------------------- | ------------------------- | ----------------------------- |
| GET    | `<course_id>`                        | URL: course id                                           | Owner, student, superuser | 200: `[AssignmentSerializer]` |
| POST   | `` (root)                            | `title`, `description`, `due_date`, `course`, `proofs[]` | Instructor (own course)   | 201                           |
| DELETE | `assignments/detail/<assignment_id>` | URL: id                                                  | Owner, superuser          | 204                           |
| PATCH  | `assignments/detail/<assignment_id>` | Partial assignment fields + `proofs[]`                   | Owner, superuser          | 200                           |


**Proofs array item:** `{ id, type: "equationalproof"|"inductionproof", name, order }`

**AssignmentSerializer:** `{ id, title, description, due_date, course, proofs[] }`

**Student proof status:** `"Not Started"` | `"In Progress"` | `"Completed"`

### Progress & library


| Method | Path                                   | Roles                 | Response                                                                                                                 |
| ------ | -------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| GET    | `assignments/<assignment_id>/progress` | Instructor, superuser | `{ columns[], students[] }` with per-proof statuses: `"not started"`, `"in progress"`, `"complete"`, `"late"`, `"error"` |
| GET    | `instructor/library`                   | Any (own proofs)      | `[{ id, name, type, displayType, tag }]`                                                                                 |




### Roster & enrollment


| Method | Path             | Body                               | Notes                               |
| ------ | ---------------- | ---------------------------------- | ----------------------------------- |
| POST   | `check-user`     | `{ student: string }`              | username or email; 200 empty or 404 |
| POST   | `add-student`    | `{ course: int, student: string }` | 201 invitation; 409 disambiguation  |
| POST   | `remove-student` | `{ course: int, student: string }` | 204                                 |
| POST   | `join-course`    | `{ code: string }`                 | 200 + course object                 |
| POST   | `leave-course`   | `{ course: int }`                  | 200                                 |




### Invitations


| Method | Path                              | Body                               | Response                       |
| ------ | --------------------------------- | ---------------------------------- | ------------------------------ |
| GET    | `courses/<course_id>/invitations` | —                                  | `[CourseInvitationSerializer]` |
| DELETE | `courses/<course_id>/invitations` | `{ invitation_id }`                | 204                            |
| GET    | `invitations/me`                  | —                                  | Pending invitations for caller |
| POST   | `invitations/me`                  | `{ invitation_id, action: "accept" | "reject" }`                    |




### Sharing


| Method | Path                        | Body / query                                                                                                                       | Notes                                                 |
| ------ | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| GET    | `assignments/shares`        | query: `course_id` (required)                                                                                                      | `{ incoming[], sent[] }`                              |
| POST   | `assignments/shares`        | Send: `{ source_course_id, target_course_id, title, description?, due_date, proofs[] }` OR respond: `{ share_request_id, action }` | 201 or 200                                            |
| DELETE | `assignments/shares`        | `{ share_request_id }`                                                                                                             | Sender only                                           |
| GET    | `instructors/share-targets` | —                                                                                                                                  | `[{ id, displayName, courses[] }]` — instructors only |




### Start assignment proof


| Method | Path                                                 | Body                                       | Response            |
| ------ | ---------------------------------------------------- | ------------------------------------------ | ------------------- |
| POST   | `assignments/<assignment_id>/start-assignment-proof` | `{ proof_id, proof_type: "equationalproof" | "inductionproof" }` |


---



## Known issues


| Issue                   | Detail                                                                                                           |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Three proof APIs        | equational + induction (canonical) vs legacy `proof/`                                                            |
| `edit-proof` mismatch   | Client: `PUT .../edit-proof/<id>`. Server: `edit=proof/<id>`                                                     |
| `/proofs` no auth       | delete and edit have no ownership checks                                                                         |
| Legacy `set-proof`      | Success returns `"isValid": "True"` (string, not bool)                                                           |
| Legacy `use-definition` | GET method, not POST                                                                                             |
| `COURSE_APIS.md` drift  | Some paths differ (e.g. share GET uses query param `course_id`)                                                  |
| Error strings           | Not stable — assert structure only in contract tests                                                             |
| DRF permissions         | Many endpoints lack explicit `@IsAuthenticated`; unauthenticated calls get broken behavior rather than clean 401 |


---



## Source files


| Prefix       | Routes                             | Views                               |
| ------------ | ---------------------------------- | ----------------------------------- |
| auth         | `accounts/urls.py`                 | `accounts/views.py`                 |
| equational   | `equational_reasoning_api/urls.py` | `equational_reasoning_api/views.py` |
| induction    | `induction_api/urls.py`            | `induction_api/views.py`            |
| legacy proof | `racket_api/urls.py`               | `racket_api/views.py`               |
| proofs       | `proofs/urls.py`                   | `proofs/views.py`                   |
| assignments  | `assignments/urls.py`              | `assignments/views.py`              |


**Integration test references:**

- `django_server/equational_reasoning_api/test_integration.py`
- `django_server/induction_api/tests.py` (+ `test_*.py` siblings)
- `django_server/assignments/tests/`

