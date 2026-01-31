# Mac Development Setup Guide - Induction Racket Application

This document outlines the complete setup process for running the Induction Racket application on macOS, including database, backend, and frontend configuration.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [MySQL Database Setup](#mysql-database-setup)
3. [Backend Setup (Python Virtual Environment)](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running Tests](#running-tests)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have the following installed:
- **Homebrew** (macOS package manager)
- **Node.js** and **npm** (for frontend)
- **Python 3.x** (for backend)
- **Git** (for version control)

To install Homebrew if not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## MySQL Database Setup

### 1. Install MySQL using Homebrew
```bash
brew install mysql
```

### 2. Start MySQL Service
```bash
brew services start mysql
```

### 3. Verify MySQL Installation
```bash
mysql --version
```

### 4. Create Database (if needed)
```bash
mysql -u root -p
```
Then in the MySQL prompt:
```sql
CREATE DATABASE proof_buddy;
EXIT;
```

---

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd /path/to/your/project/backend
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment
```bash
source venv/bin/activate
```
*Note: You should see `(venv)` prefix in your terminal prompt*

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run Database Migrations (if applicable)
```bash
python manage.py migrate
```

### 7. Start Backend Server
```bash
python manage.py runserver
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd /path/to/your/project/frontend
```

### 2. Install Node Dependencies
```bash
npm install
```

### 3. Install Testing Dependencies (if not included)
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

### 4. Configure API Endpoint
Ensure your frontend is configured to connect to the backend. Check configuration files like:
- `src/config.js`
- `.env` or `.env.local`

Example `.env.local`:
```env
REACT_APP_API_URL=http://localhost:5000
```

### 5. Start Frontend Development Server
```bash
npm start
```

The application should open automatically in your browser at `http://localhost:3000`

---

## Running Tests

### 1. Run InductionRacket Component Tests
```bash
npm test src/pages/InductionRacket.test.js
```

### 2. Run All Tests
```bash
npm test
```

### 3. Run Tests in Watch Mode
```bash
npm test -- --watch
```

### 4. Run Tests with Coverage
```bash
npm test -- --coverage
```

---

## Verification

### Verify MySQL is Running
```bash
brew services list | grep mysql
```
Should show `started` status

### Verify Frontend is Running
Open browser to `http://localhost:3000` and check:
- Page loads without errors
- "Induction: Racket" header is visible
- All form fields are present (Name, # Tag, IVar, AVal, LVar)
- Console has no errors

### Verify Tests Pass
All tests in `InductionRacket.test.js` should pass:
- Component rendering tests
- Form input handling tests
- Validation logic tests
- Button interaction tests

---

## Troubleshooting

### MySQL Connection Issues
**Problem**: Cannot connect to MySQL
```bash
# Check if MySQL is running
brew services list

# Restart MySQL
brew services restart mysql

# Check MySQL logs
tail -f /usr/local/var/mysql/*.err
```

### Virtual Environment Issues
**Problem**: Cannot activate virtual environment
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use
**Problem**: Port 3000 or 5000 already in use
```bash
# Find process using port
lsof -i :3000
lsof -i :5000

# Kill process
kill -9 <PID>
```

### Node Module Issues
**Problem**: Module not found errors
```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### Test Failures
**Problem**: Tests failing unexpectedly
```bash
# Clear Jest cache
npm test -- --clearCache

# Run tests in verbose mode
npm test -- --verbose
```

---

## Common Commands Reference

### Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Run backend server
python app.py
```

### Frontend
```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### MySQL
```bash
# Start MySQL
brew services start mysql

# Stop MySQL
brew services stop mysql

# Access MySQL CLI
mysql -u root -p
```

---

---

## Notes

- Always activate the virtual environment before working on backend code  
- Keep dependencies up to date in `requirements.txt` and `package.json`  
- Commit `.env.example` files but never commit actual `.env` files with credentials  
- Run tests before committing changes  
- Use `brew services` to manage MySQL instead of manual starts/stops  

---
