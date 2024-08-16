#!/bin/bash

# Generate the setup.sql file with environment variables
cat << EOF > /docker-entrypoint-initdb.d/setup.sql
CREATE DATABASE IF NOT EXISTS \`${DATABASE_NAME}\`;

CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${MARIADB_ROOT_PASSWORD}';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
EOF

# Execute the generated setup.sql file
mysql < /docker-entrypoint-initdb.d/setup.sql
