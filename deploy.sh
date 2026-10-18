#!/bin/bash
set -e
git pull
sudo docker compose build
sudo docker compose up -d --force-recreate
