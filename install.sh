#!/usr/bin/env bash
set -euo pipefail

APP_NAME="volumio-screensaver"
APP_DIR="/opt/${APP_NAME}"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
ENV_FILE="/etc/${APP_NAME}.env"
REPO_URL="${REPO_URL:-https://github.com/arut16/Ecran-Veille-Volumio.git}"

if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR=""

cleanup() {
  if [[ -n "${TMP_DIR}" && -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}
trap cleanup EXIT

apt-get update
apt-get install -y \
  git \
  python3 \
  python3-dev \
  python3-pip \
  python3-venv \
  python3-pil \
  python3-numpy \
  python3-spidev \
  libgpiod2 \
  fonts-dejavu-core \
  build-essential

RPI_GPIO_FROM_PIP=0
if ! apt-get install -y python3-rpi.gpio; then
  RPI_GPIO_FROM_PIP=1
fi

if [[ -d "${SCRIPT_DIR}/volumio_screensaver" ]]; then
  SOURCE_DIR="${SCRIPT_DIR}"
else
  TMP_DIR="$(mktemp -d)"
  git clone --depth=1 "${REPO_URL}" "${TMP_DIR}"
  SOURCE_DIR="${TMP_DIR}"
fi

mkdir -p "${APP_DIR}"
python3 -m venv --system-site-packages "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/python" -m pip install --upgrade pip setuptools wheel
"${APP_DIR}/venv/bin/python" -m pip install "${SOURCE_DIR}"

if [[ "${RPI_GPIO_FROM_PIP}" -eq 1 ]]; then
  "${APP_DIR}/venv/bin/python" -m pip install RPi.GPIO
fi

install -m 0644 "${SOURCE_DIR}/systemd/${APP_NAME}.service" "${SERVICE_FILE}"

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 0644 "${SOURCE_DIR}/config/${APP_NAME}.env.example" "${ENV_FILE}"
fi

systemctl daemon-reload
systemctl enable "${APP_NAME}.service"
systemctl restart "${APP_NAME}.service"

echo
echo "Installation terminee."
echo "Etat du service : sudo systemctl status ${APP_NAME}"
echo "Logs en direct  : sudo journalctl -u ${APP_NAME} -f"
