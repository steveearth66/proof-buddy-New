#!/bin/bash
git pull
sudo docker compose up --build -d --force-recreate
