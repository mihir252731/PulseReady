#!/usr/bin/env bash
export TEAM_KEY=${TEAM_KEY:-CHANGE_ME}
export ADMIN_USER=${ADMIN_USER:-admin}
export ADMIN_PASS=${ADMIN_PASS:-admin}
export JWT_SECRET=${JWT_SECRET:-dev_secret_change_me}
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
