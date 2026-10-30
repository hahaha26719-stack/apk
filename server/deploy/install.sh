#!/usr/bin/env bash
#
# Install the Ohr Temimim Attendance server as a systemd service on Linux.
# The service listens on port 8000 and starts automatically on boot.
#
# Usage (run from the server/ directory, with sudo):
#     sudo bash deploy/install.sh
#
set -euo pipefail

# ---- Resolve paths ----
# APP_DIR = the server/ directory (one level up from this script's deploy/ folder).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# The user the service runs as: the owner of the files (not root, if possible).
RUN_USER="${SUDO_USER:-$(stat -c '%U' "$APP_DIR")}"
SERVICE_NAME="ohr-temimim"

echo "==> App directory : $APP_DIR"
echo "==> Run as user   : $RUN_USER"

# ---- Python virtualenv + dependencies ----
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed." >&2
  exit 1
fi

# On ARM boards (Banana Pi, Raspberry Pi, etc.) pip must compile bcrypt/cffi from
# source, which needs compilers and headers. Install them if apt is available.
# All Python deps are pure-Python wheels (no native/Rust builds), so only
# python3-venv is needed. Install it if apt is available.
if command -v apt-get >/dev/null 2>&1; then
  echo "==> Ensuring python3-venv is installed..."
  apt-get update -y
  apt-get install -y python3-venv
fi

echo "==> Creating virtualenv and installing dependencies..."
sudo -u "$RUN_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$RUN_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip >/dev/null
sudo -u "$RUN_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# ---- Production secrets ----
if [ ! -f "$APP_DIR/.env" ]; then
  echo "==> Creating $APP_DIR/.env from .env.example (EDIT THIS before going live!)"
  cp "$APP_DIR/deploy/.env.example" "$APP_DIR/.env"
  # Generate a random SECRET_KEY.
  RAND="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$RAND|" "$APP_DIR/.env"
  chown "$RUN_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi

# ---- Install systemd unit ----
echo "==> Installing systemd service: $SERVICE_NAME"
UNIT_SRC="$APP_DIR/deploy/ohr-temimim.service"
UNIT_DST="/etc/systemd/system/$SERVICE_NAME.service"
sed -e "s|__USER__|$RUN_USER|g" -e "s|__APP_DIR__|$APP_DIR|g" "$UNIT_SRC" > "$UNIT_DST"

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "============================================================"
echo " Ohr Temimim server installed and started on port 8000."
echo " It will now start automatically on every boot."
echo ""
echo " Status : sudo systemctl status $SERVICE_NAME"
echo " Logs   : sudo journalctl -u $SERVICE_NAME -f"
echo " Restart: sudo systemctl restart $SERVICE_NAME"
echo " Stop   : sudo systemctl stop $SERVICE_NAME"
echo ""
echo " Admin panel: http://<this-server-ip>:8000"
echo " IMPORTANT: edit $APP_DIR/.env and change the admin password!"
echo "============================================================"
