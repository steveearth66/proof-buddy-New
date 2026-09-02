# Proof Buddy

A web application for verifying mathematical proofs using Equational Reasoning with Racket. It is capable of symbolic manipulation and structural induction. It is currently utilized by professors and students in courses at Drexel University.



## Table of Contents

- [Prerequisites](#prerequisites)

- [Local Installation](#local-installation)

- [Env File Setup](#env-file-setup)

- [Running the Application](#running-the-application)

- [Developer Documentation](#developer-documentation)

- [Feature Guides](#feature-guides)

- [Testing](#testing)

- [Deployment & Setup Reference](#deployment--setup-reference)

- [API Reference](#api-reference)

- [Project Context & Legacy](#project-context--legacy)



## Prerequisites



Before starting with the installation process, ensure you have the following installed:



- [Node.js and npm](https://nodejs.org/en/download/)

- [Python installation](https://www.python.org/downloads/release/python-3122/)

- [MySQL](https://dev.mysql.com/downloads/installer/)



## Local Installation



- For first time project set up instruction on your local machine, please view: documentation/user_documentation/local_installation/documentation/readme_resources/1_first_time_project_set_up.md

    - [First Time Project Setup](documentation/user_documentation/local_installation/documentation/readme_resources/1_first_time_project_set_up.md)

- For macOS-specific first time project set up, please view: documentation/user_documentation/local_installation/documentation/readme_resources/MacOS_Development_Setup_Guide.md

    - [macOS Development Setup](documentation/user_documentation/local_installation/documentation/readme_resources/MacOS_Development_Setup_Guide.md)



## Env File Setup



- For how to create a /.env file on your local machine, please view: documentation/user_documentation/local_installation/documentation/readme_resources/2_env_file_first_set_up.md

    - [First /.env Setup](documentation/user_documentation/local_installation/documentation/readme_resources/2_env_file_first_set_up.md)



## Running the Application



- For instructions for running the application, please view: documentation/user_documentation/local_installation/documentation/readme_resources/3_running_application.md

    - [Running the application](documentation/user_documentation/local_installation/documentation/readme_resources/3_running_application.md)



## Developer Documentation



Essential reading for developers working on Proof Buddy internals.



- For where core logic lives and how to extend the system, please view: DEVELOPER_GUIDE.md

    - [Developer Guide](DEVELOPER_GUIDE.md) — proof engine, rules, API views, frontend pages; how to add rules and UDFs

- For system architecture and major subsystems, please view: ARCHITECTURE.md

    - [Architecture](ARCHITECTURE.md) — frontend, backend apps, proof engine, cache, database, deployment stack

- For a map of every significant directory and file, please view: DIRECTORY_MAP.md

    - [Directory Map](DIRECTORY_MAP.md) — repo orientation for new developers

- For end-to-end request and data traces, please view: DATA_FLOW.md

    - [Data Flow](DATA_FLOW.md) — auth, proof sessions, rule application, cache, and database

- For a consolidated local setup and development workflow reference, please view: SETUP.md

    - [Setup Guide](SETUP.md) — prerequisites, env vars, MySQL, backend/frontend, Docker overview



## Feature Guides



Documentation for specific product features and modules.



- For lemma creation and application, please view: documentation/user_documentation/Lemma/LEMMA.md

    - [Lemma Guide](documentation/user_documentation/Lemma/LEMMA.md) — completing proofs as lemmas; `apply` keyword; data model

- For instructor and student course workflows, please view: documentation/user_documentation/Courses/COURSE_USER_INSTRUCTIONS.md

    - [Course User Instructions](documentation/user_documentation/Courses/COURSE_USER_INSTRUCTIONS.md) — creating courses, enrollments, assignments

- For courses module architecture and schema, please view: documentation/user_documentation/Courses/COURSE_DEVELOPER_NOTES.md

    - [Course Developer Notes](documentation/user_documentation/Courses/COURSE_DEVELOPER_NOTES.md) — roles, ownership checks, database layout



## Testing



- For manual browser QA of equational reasoning, please view: TESTING_GUIDE.md

    - [Manual QA Checklist](TESTING_GUIDE.md) — step-by-step smoke tests in the browser

- For backend test suite organization, please view: django_server/proofs/TEST_STRUCTURE.md

    - [Test Structure](django_server/proofs/TEST_STRUCTURE.md) — Django test modules and how to run them



## Deployment & Setup Reference



Additional setup and deployment guides beyond the local installation chain above.



- For macOS-specific setup, please view: documentation/user_documentation/local_installation/documentation/readme_resources/MacOS_Development_Setup_Guide.md

    - [macOS Development Setup](documentation/user_documentation/local_installation/documentation/readme_resources/MacOS_Development_Setup_Guide.md)

- For Docker deployment, please view: documentation/docker/docker_usage.md

    - [Docker Usage](documentation/docker/docker_usage.md)



## API Reference



- **Primary:** [API Reference](documentation/user_documentation/API_REFERENCE.md) — current HTTP API documentation (routes, parameters, responses).

- **Induction:** [induction_api/README.md](django_server/induction_api/README.md) — induction endpoints with curl examples and usage flow.

- **Courses:** [COURSE_APIS.md](documentation/user_documentation/Courses/COURSE_APIS.md) — courses and assignments API spec (some paths may differ from code; cross-check with primary API reference).

- **Legacy:** [4_API_reference.md](documentation/user_documentation/local_installation/documentation/readme_resources/4_API_reference.md) — older auth-only stub; not kept up to date (some paths no longer match the API). Retained for existing install-doc links.



## Project Context & Legacy



Background, in-progress work, and historical or outdated documentation.



- For pedagogical background and proof-type overview, please view: RESEARCH_CONTEXT.md

    - [Research Context](RESEARCH_CONTEXT.md) — why Proof Buddy exists; equational reasoning and induction

- For list induction work in progress, please view: LIST_INDUCTION_PROGRESS.md

    - [List Induction Progress](LIST_INDUCTION_PROGRESS.md) — active feature tracker

- **Historical planning:** [EquationalReasoningPlan.txt](EquationalReasoningPlan.txt) · [EquationalReasoningStatus.txt](EquationalReasoningStatus.txt) · [eqrnPlan.txt](eqrnPlan.txt)

- **Outdated:** [OUTDATED_Google_Cloud_Configuration.md](documentation/user_documentation/local_installation/documentation/readme_resources/OUTDATED_Google_Cloud_Configuration.md) — legacy GCP deployment; do not use

- **Boilerplate:** [client/README.md](client/README.md) — default Create React App readme
