# API Specifications: Courses & Assignments Module

This document outlines the APIs for the Courses and Assignments system. All endpoints require user authentication via an active authorization token header.

---

## 1. Course Views (`CourseViewSet`)

### `GET` /courses

Lists all active relevant courses based on the requesting user's account role.

* **Authentication Required:** `Yes`
* **Access Scope:** `All Authenticated Users`
* **Behavior:** Instructors see courses they own along with courses they have joined as an observer. Students only see courses where `is_active=True`.

#### Expected Responses

* **Success (`200 OK`)**

```json
[
    {
        "id": 42,
        "name": "Test 2",
        "instructor": {
            "id": 3,
            "email": "testmail@mail.com",
            "username": "int566",
            "first_name": "John",
            "last_name": "Instructor"
        },
        "students": [
        {
            "id": 4,
            "email": "teststu@mail.com",
            "username": "test22",
            "first_name": "John",
            "last_name": "Test"
        }
        ],
        "join_code_expires_at": "2026-05-17 02:29:11.926406",
        "created_by": {
            "id": 3,
            "email": "testmail@mail.com",
            "username": "int566",
            "first_name": "John",
            "last_name": "Instructor"
        },
        "is_active": true,
        "term": "Fall 2025",
        "description": "Course Description"
    }
]
```

### `GET` /courses/<course_id>

Fetches the details of a specific course by its unique database ID.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner, Enrolled Students, or Superusers

* **Behavior:** Blocks a student from viewing if the course is marked inactive (is_active=False).

#### Expected Responses

* **Success (`200 OK`)**

See the [success json](#expected-responses) from /courses for a sample json. Instead of a list, this returns just a single course.

* **Failure (`403 Forbidden`)**

```json
{ 
    "message": "You are not authorized to view this course." 
}
```

* **Failure (`404 Not Found`)**

```json
{ 
    "message": "Course not found"
}
```

### `POST` /courses

Creates a brand new course instance.

* **Authentication Required:** Yes

* **Access Scope:** Instructors and Superusers Only

#### Request Parameters & Body

The name is the only required value for this api. Optional fields include: students, generate_join_code, and exipration_date. The students parameter must contain a list of student usernames or emails that is used to set the initial list of students for the course. The generate_join_code parameter set to true will note the system to create one, and the expiration_date will set the time the code expires (7 days default if omitted).

```json
{
    "name": "name",
    "generate_join_code": true
}
```

#### Expected Responses

* **Success (`201 Created`)**

See the [success json](#expected-responses) from /courses for a sample json. Instead of a list, this returns just a single course.

* **Failure (`400 Bad Request`)**

```json
{ 
    "name": ["This field is required."]
}
```

or

```json
{
    "message": "Course ID is required."
}
```

* **Failure (`403 Forbidden`)**

```json
{ 
    "message": "You are not authorized to create a course."
}
```

### `PATCH` /courses/<course_id>

Updates course parameters dynamically, or handles custom code token generation.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner or Superuser Only

#### Regenerate Join Code

Request Payload

```json
{ 
    "action": "regenerate_code"
}
```

Expected Responses

* **Success (`200 OK`)**

```json
{
    "join_code": "AB78X9WY",
    "join_code_expires_at": "2026-05-30T14:00:00Z"
}
```

#### Modify Course Data

Any modification that is not to regenerate the join code is handled by passing the values desired to be updated in the payload. The example below would set the is_active value to true.

Request Payload

```json
{
    "is_active": true
}
```

Expected Responses

* **Success (`200 OK`)**

  * See the [success json](#expected-responses) from /courses for a sample json. Instead of a list, this returns just a single course.

* **Failure (`400 Bad Request`)**

```json
{ 
    "name": ["This field is required."]
}
```

## 2. Assignment View (`AssignmentViewSet`)

### `GET` /<course_id>

Lists all assignments associated with a particular course ID. If the requesting user is an instructor, the response will return no information about student proofs. If the user is a student on the course, then this response will include information about the student's progress on each proof.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner, Enrolled Students, or Superusers

#### Expected Responses

* **Success (`200 OK`)**

```json
[
    {
        "id": 6,
        "title": "Test 2",
        "description": "No Description Provided",
        "due_date": "2026-12-12T00:00:00-05:00",
        "created_by": {
            "id": 3,
            "email": "testmail@mail.com",
            "username": "int566",
            "first_name": "John",
            "last_name": "Instructor"
        },
        "proofs": [
            {
                "id": 1,
                "name": "Proof Name",
                "tag": "tag",
                "type": "equationalproof",
                "displayType": "Equational Reasoning",
                "status": "Not Started",
                "student_proof_id": 3,
                "is_locked": true
            }
        ]
    }
]
```

### `POST` /

Creates an assignment for a course.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner or Superuser Only

#### Request Parameters & Body

```json
{
    "id": null,
    "title": "Assignment Title",
    "description": "No Description Provided",
    "due_date": "2024-12-12",
    "course": 1,
    "proofs": [
        {
            "id": 1,
            "type": "equationalproof",
            "name": "Proof Name",
            "order": 0
        }
    ]
}
```

#### Expected Responses

* **Success (`201 Created`)**
  * Returns the created assignment.

```json
{
    "id": null,
    "title": "Assignment Title",
    "description": "No Description Provided",
    "due_date": "2024-12-12",
    "course": 1,
    "proofs": [
        {
            "id": 1,
            "type": "equationalproof",
            "name": "Proof Name",
            "order": 0
        }
    ]
}
```

* **Failure (`400 Bad Request`)**
  * Assignment data from the payload is incorrect.

```json
{
    "title": ["This field is required."]
}
```

* **Failure (`403 Forbidden`)**

If the requesting user account is not an instructor:

```json
{
    "message": "You are not authorized to create an assignment."
}
```

If the account is an instructor but does not own the course:

```json
{
    "message": "You can only create assignments for your own courses."
}
```

* **Failure (`404 Not Found`)**

```json
{
    "message": "Course not found"
}
```

## 3. Assignment Detail View (`AssignmentDetailView`)

### `DELETE` assignments/detail/<assignment_id>

Deletes an assignment from the database. This triggers a cascade wipe of mappings and submissions.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner or Superuser Only

#### Expected Responses

* **Success (`204 No Content`)**
Response body is empty.

### PATCH /assignments/detail/<assignment_id>

Partially updates an assignment's configurations.

* **Authentication Required:** Yes

* **Access Scope:** Course Owner or Superuser Only

#### Request Parameters & Body

The payload should contain all of the fields that are to be changed. The example below changes the title to "Revised Title Name".

```json
{
    "title": "Revised Title Name"
}
```

#### Expected Responses

* **Success (`200 OK`)**

See the [post success json](#expected-responses-4) from AssignmentSetView for a sample json. The full assignment information is returned, not just the updated part.

* **Failure (`400 Bad Request`)**

```json
{
    "title": ["This field is required."]
}
```

## 4. Assignment Progress View (`AssignmentProgressMatrixView`)

### `GET` /assignments/<assignment_id>/progress

Assembles a complete evaluation overview framework for instructors to track assignment completion status for all students across all proofs on an assignment.

#### Expectred Responses

* **Success (`200 OK`)**

```json
{
    "columns": [
        {
            "id": 1,
            "title": "Proof 1",
            "type": "equationalproof"
        }
    ],
    "students": [
        {
            "id": 3,
            "username": "stu1234",
            "email": "student@email.com",
            "firstName": "Mark",
            "lastName": "Student",
            "statuses": {
                "1": {
                    "status": "not started",
                    "cloned_proof_id": null,
                    "proof_type": null
                }
            }
        }
    ]
}
```

* **Failure (`403 Forbidden`)**

```json
{
    "message": "You are not authorized to view progress for this assignment."
}
```

* **Failure (`404 Not Found`)**
  * No special message is returned.

## 5. Instructor Library View (`InstructorLibraryView`)

### `GET` /instructor/library

Gathers all valid equational and induction proofs belonging to the requesting user. Data included in the response is intended for use in selecting proofs for creating an assignment.

* **Authentication Required:** Yes
* **Access Scope:** Instructors Only (Intended), Any User can call because it only returns a list of their proofs.

#### Expected Responses

* **Success (`200 OK`)**
  * The response for this call will always contain a list of proofs. If the user has no proofs, an empty list is returned.

```json
[
    { 
        "id": 1, 
        "name": "Proof 1", 
        "type": "equationalproof", 
        "displayType": "Equational Reasoning", 
        "tag": "tag" 
    },
    { 
        "id": 2, 
        "name": "Proof 2", 
        "type": "inductionproof", 
        "displayType": "Induction", 
        "tag": "tag" 
    }
]
```

## 6. Course Invitation View (`CourseInvitationView`)

### `GET` courses/<course_id>/invitations

Instructors list all generated invitations active for a course.

* **Authentication Required:** Yes
* **Access Scope:** Course Owner Only

#### Expected Responses

```json
[
    {
        "id": 1, 
        "course": 2,
        "course_name": "Course I own", 
        "instructor_name": "John Instructor", 
        "student": 3,
        "status": "pending", 
        "sent_at": "2026-05-30T14:00:00Z"
    }
]
```

### `DELETE` courses/<course_id>/invitations

Delete a previously sent student course invitation. Only the owner of a course can delete student invitations for their course.

* **Authentication Required:** Yes
* **Access Scope:** Course Owner Only

#### Request Parameters & Payload

```json
{
    "invitation_id": 1
}
```

#### Expected Responses

* **Success (`204 No Content`)**
* **Failure (`404 Not Found`)**
  * No special message is returned.

## 7. Student Invitation View (`StudentInvitationView`)

### `GET` invitations/me

Allows an authenticated student account to review their own pending course requests.

* **Authentication Required:** Yes
* **Access Scope:** Target Student Profile Only

#### Expected Responses

* **Success (`200 OK`)**

```json
[
    {
        "id": 1, 
        "course": 2,
        "course_name": "Course I am enrolled in", 
        "instructor_name": "John Instructor", 
        "student": 3,
        "status": "pending", 
        "sent_at": "2026-05-30T14:00:00Z"
    }
]
```

### `POST` invitations/me

Allows students to either accept or reject a pending course invitation. This will not delete the invitation, only change it's status.

* **Authentication Required:** Yes
* **Access Scope:** Target Student Profile Only

#### Request Parameters & Body

```json
{
    "invitation_id": 1,
    "action": "accept"
}
```

Possible actions are "accept" and "reject" for the student to either accept the invitation or reject it.

#### Expected Responses

* **Success (`200 OK`)**
  * Action = "accept"

    ```json
    {
        "message": "Joined course."
    }
    ```

  * Action = "reject"
  
    ```json
    {
        "message": "Invitation declined."
    }
    ```

* **Failure (`400 Bad Request`)**

```json
{
    "error": "Invalid action."
}
```

## 8. Individual APIs

### 8.1 `POST` check_user

Checks if a user exists. This was a legacy api that is now unused.

* **Authentication Required:** Yes
* **Access Scope:** Any User

### Expected Responses

* **Success (`200 OK`)**
  * No json returned.
* **Failure (`404 Not Found`)**

```json
{
    "message": "User not found"
}
```

### 8.2 `POST` remove_student

Drops a target student directly from a course roster.

* **Authentication Required:** Yes
* **Access Scope:** Course Owner or Superuser Only

#### Request Parameters & Body

```json
{
    "course": 1,
    "student": "student1"
}
```

> [!NOTE]
> The student can be referenced by username or email.

#### Expected Responses

* **Success (`204 No Content`)**
* **Failure (`403 Forbidden`)**

```json
{
    "message": "You are not authorized to remove a student from this course."
}
```

* **Failure (`404 Not Found`)**
A 404 is returned if the course does not exist:

```json
{
    "message": "Course not found"
}
```

or if the user does not exist:

```json
{
    "message": "User not found"
}
```

### 8.3 `POST` add_student

Creates a course invitation or sets an existing invitation back to a pending state.

* **Authentication Required:** Yes
* **Access Scope:** Course Owner or Superuser Only

#### Request Parameters & Body

```json
{
    "course": 1,
    "student": "student1"
}
```

#### Expected Responses

* **Success (`200 OK`)**

```json
{
    "message": "Existing invitation updated to pending.",
    "invitation": {
        "id": 1,
        "course": 2,
        "course_name": "my course",
        "instructor_name": "John Instructor",
        "student": 3,
        "status": "pending",
        "sent_at": "2026-05-30T14:00:00Z"
    }
}
```

* **Success (`201 CREATED`)**

```json
{
    "invitation": {
        "id": 1,
        "course": 2,
        "course_name": "my course",
        "instructor_name": "John Instructor",
        "student": 3,
        "status": "pending",
        "sent_at": "2026-05-30T14:00:00Z"
    }
}
```

* **Success (`204 No Content`)**

```json
{
    "message": "Student is already in the course."
}
```

* **Failure (`400 Bad Request`)**

```json
{
    "message": "Instructors cannot be added as students."
}
```

* **Failure (`403 Forbidden`)**

```json
{
    "message": "You are not authorized to add a student to this course."
}
```

* **Failure (`404 Not Found`)**
  * A 404 error is possible when checking existence of the course:

    ```json
    {
        "message": "Course not found"
    }
    ```

    or when checking for existence of the student:

    ```json
    {
        "message": "Student not found. Check the spelling and try again."
    }
    ```

* **Failure (`409 Conflict`)**
  * Username uniqueness makes this response only possible when searching by email to add a student. Complete the request again using one of the usernames in the list to succeed in making the student invitation.

```json
{
    "message": "Multiple students share this identifier. Please select the correct one.",
    "requires_disambiguation": true,
    "candidates": [
        {
            "username": "student1",
            "email": "student1@email.com",
            "name": "No Name Provided"
        },
        {
            "username": "student2",
            "email": "student1@email.com",
            "name": "Mark Student"
        }
    ]
}
```

### 8.4 `POST` join_course

Processes immediate enrollment using a matching unexpired join code.

* **Authentication Required:** Yes
* **Access Scope:** Authenticated Students

#### Request Parameters & Body

```json
{
    "code": "AB78X9WY"
}
```

#### Expected Responses

* **Success (`200 OK`)**

```json
{
    "message": "Successfully joined the course!",
    "course": {
        "id": 1,
        "name": "Course 1",
        "instructor": {
            "username": "inst1",
            "firt_name": "John",
            "last_name": "Instructor"
        },
        "is_active": true, 
        "term": "Summer 2026", 
        "description": "Course Description"
    }
}
```

* **Failure (`400 Bad Request`)**

A 400 will be returned if the join code is not provided:

```json
{
    "message": "Please provide a join code."
}
```

or if the user is already in the course:

```json
{
    "message": "You are already enrolled in this course."
}
```

### 8.5 `POST` leave_course

Allows a student to voluntarily remove themselves from a course roster.

* **Authentication Required:** Yes
* **Access Scope:** Authenticated Students

#### Request Parameters & Body

```json
{
    "course": 2
}
```

#### Expected Responses

* **Success (`200 OK`)**

```json
{
    "message": "Successfully left the course."
}
```

* **Failure (`400 Bad Request`)**

```json
{
    "message": "You are not enrolled in this course."
}
```

* **Failure (`404 Not Found`)**

```json
{
    "message": "Course not found"
}
```

### 8.6 `POST` start_assignment_proof

Creates a copy of an assignment proof for the student to use. Couples the student's new proof with the existing assignment.

* **Authentication Required:** Yes
* **Access Scope:** Enrolled Students

#### Request Parameters & Body

```json
{
    "proof_id": 14,
    "proof_type": "equationalproof"
}
```

#### Expected Responses

* **Success (`200 OK`)**

```json
{
    "success": true,
    "new_proof_id": 15,
    "type": "equationalproof"
}
```

* **Success (`201 Created`)**
  * This returns the same json as a 200, but the status code denotes the database was updated.

```json
{
    "success": true,
    "new_proof_id": 15,
    "type": "equationalproof"
}
```

* **Failure (`400 Bad Request`)**

```json
{
    "message": "Proof ID and type are required."
}
```

* **Failure (`404 Not Found`)**

```json
{
    "message": "Template proof not found."
}
```
