#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/var/www/legendscope"
PYTHON_BIN="python3.11"
SERVICE_NAME="legendscope"

if [ ! -d "$PROJECT_ROOT" ]; then
  sudo mkdir -p "$PROJECT_ROOT"
  sudo chown "$USER":"$USER" "$PROJECT_ROOT"
fi

rsync -a --delete app "$PROJECT_ROOT"/
rsync -a requirements.txt "$PROJECT_ROOT"/
rsync -a pyproject.toml "$PROJECT_ROOT"/
rsync -a .env.example "$PROJECT_ROOT"/

cd "$PROJECT_ROOT"

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

deactivate

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.service"
sudo systemctl restart "${SERVICE_NAME}.service"
