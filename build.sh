#!/usr/bin/env bash
# build.sh — Render build script for PantryFlow backend
set -o errexit

pip install -r backend/requirements.txt
python backend/manage.py collectstatic --no-input
python backend/manage.py migrate
