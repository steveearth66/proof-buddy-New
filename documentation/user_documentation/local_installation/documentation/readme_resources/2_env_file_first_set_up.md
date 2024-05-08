1. Create and configure the environment variables in the `.env` file under /django_server like so:

<br>

2. Make sure that DB_HOST equals "localhost".
3. Make sure DB_USER equal "root".
4. Make sure DB_PASSWORD equals the password you created when you installed MySQl Workbench. If you opted for no password, leave this an empty String.
5. Make sure DB_NAME equals the name of the Schema you created in MySQl Workbench. If you followed the tutorial, this will be "proof_buddy_development".
6. Make sure DB_PORT is set to whatever port your database is running on.
7. DEBUG should be True for development and False for production.
8. SECRET_KEY can be generated online. (Google generate secret key for django)
9. EMAIL_HOST should be host of email server.
10. EMAIL_PORT should be port email server is running on.
11. EMAIL_HOST_USER should be the email address of the account.
12. EMAIL_HOST_PASSWORD password of the email host. (If using google as email server look into adding an app password)
13. FRONTEND_URL url proofbuddy is accessible by.
14. BACKEND_URL url the backend will hosted on.
15. Final note: Never push your .env file to Github or share it on any public forum. This will cause a security risk for yourself. Presently, the .gitignore is set up to ignore these files.

```
# Database configurations.
DB_NAME=proof_buddy_development
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_PORT=3306
DEBUG=True
SECRET_KEY=SOME_SECRET_KEY

# Email configurations.
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=email@example.com
EMAIL_HOST_PASSWORD=django_app_password
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

```