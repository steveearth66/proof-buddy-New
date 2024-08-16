#!/bin/bash
apt-get update && apt-get install -y mysql-client
mysql -h localhost -u root -p$MARIADB_ROOT_PASSWORD
