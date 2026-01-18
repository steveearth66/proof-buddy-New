Common Installation & Configuration Issues 

 

1. Python/Pip Version Conflict 

 

Symptoms: 

django.core.exceptions.ImproperlyConfigured during migration 

Package installation failures 

 

Solution: 

bash 

# Force using correct Python version 
python3 -m pip install -r requirements.txt 
 
# Verify Python version 
python3 --version  # Should be 3.12.0 

 

Prevention: 

Use virtual environments: python3 -m venv venv 

Activate environment before installation 

Always use python3 -m pip instead of plain pip 

 

2. MySQL Database Configuration 

 

Symptoms: 

MySQL server runs but Django can't connect 

Missing database schemas 

 

Required Components: 

MySQL Server (version 8.0+ recommended) 

MySQL Workbench (for visual management) 

Correct connection configuration 

 

Setup Steps: 

bash 

# Install MySQL client for Python 
python3 -m pip install mysqlclient 
 
# If mysqlclient fails, use pymysql as fallback 
python3 -m pip install pymysql 

 

Configuration Fix: 
Add to both files: 

django_server/manage.py 

django_server/django_server/wsgi.py 

 

python 

# Add at the very top of each file 
import pymysql 
pymysql.install_as_MySQLdb() 

 

Environment Variables (.env file): 

env 

DB_NAME=proof_buddy 
DB_USER=your_username 
DB_PASSWORD=your_password 
DB_HOST=localhost 
DB_PORT=3306 

 

3. Branch-Specific Issues 

 

Symptoms: 

Cannot login with test accounts 

Missing proof options/features 

Incomplete functionality 

 

Solution: 

 

bash 

# Check current branch 
git branch 
 
# Switch to correct working branch 
git checkout indFront  # or whichever branch is stable 
 
# Pull latest changes 
git pull origin indFront 
 
# Re-run migrations 
python3 manage.py migrate 

 

Verification Steps: 

Confirm you're on indFront branch (not staging or main) 

Recreate test accounts after switching branches 

Clear browser cache and cookies 

Restart Django development server 

 

Quick Diagnosis Checklist 

 

Before Reporting Setup Issues: 

Python version is exactly 3.12 

Using python3 -m pip not pip 

Virtual environment activated (if using) 

MySQL Workbench installed and running 

Database connection tested in Workbench 

.env file exists with correct credentials 

On correct git branch (indFront) 

All migrations applied successfully 

 

When Login/Proof Options Missing: 

Check branch: git status 

Reset database: python3 manage.py flush 

Recreate superuser: python3 manage.py createsuperuser 

Seed test data: Ask team for fixtures or seed scripts 

Clear sessions: Delete browser cookies or use incognito mode 

 

Environment-Specific Notes 

 

macOS/Linux: 

bash 

# Common issue: Multiple Python versions 
which python3 
which pip 
 
# Solution: Use explicit paths 
/usr/bin/python3 -m pip install --user -r requirements.txt 

 

Windows: 

bash 

# Python executable might be 'py' instead 
py -m pip install -r requirements.txt 
py manage.py migrate 
 
# MySQL Workbench installation is crucial 
# Download from: https://dev.mysql.com/downloads/workbench/ 

 

 

Troubleshooting Workflow 

 

Step 1: Installation Issues 

text 

Error → Check Python version → Use python3 -m pip → Verify packages 

 

Step 2: Database Issues 

text 

Connection failed → Install Workbench → Configure the .env file → Test connection 

 

Step 3: Runtime Issues 

text 

Functionality missing → Check branch → Migrate database → Clear cache 

Emergency Shortcuts 

 

Quick Reset (When Everything Seems Broken): 

bash 

# 1. Ensure correct branch 
git checkout indFront 
git pull 
 
# 2. Reinstall dependencies 
python3 -m pip install --upgrade -r requirements.txt 
 
# 3. Reset database (CAUTION: deletes data) 
python3 manage.py reset_db 
python3 manage.py migrate 
 
# 4. Create fresh admin user 
python3 manage.py createsuperuser 
 
# 5. Restart server 
python3 manage.py runserver 

 

Getting Help 

 

Include These Details When Asking for Support: 

Your operating system 

Python version: python3 --version 

Current branch: git branch --show-current 

Error message (exact copy) 

Steps you've already tried 

 

Example Support Request: 

 

OS: macOS 12.4 
Python: 3.9.13 
Branch: indFront 
Error: "django.core.exceptions.ImproperlyConfigured" 
Tried: python3 -m pip install, verified the .env file, restarted MySQL 

 

This addendum is based on actual setup experiences. Update as new issues are discovered. 
Last Updated: 11 January 2026 
Contributor: Ahsan Nadeem 

 