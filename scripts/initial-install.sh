#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly SERVICE_USER="xmr"
readonly SERVICE_GROUP="xmr"
readonly SERVICE_FILE="/etc/systemd/system/xmr.service"

step() {
    printf '\n==> %s\n' "$1"
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "ERROR: This script must be run as root." >&2
        exit 1
    fi
}

verify_service_account() {
    id "$SERVICE_USER" >/dev/null 2>&1 ||
        { echo "ERROR: User '$SERVICE_USER' does not exist." >&2; exit 1; }

    getent group "$SERVICE_GROUP" >/dev/null 2>&1 ||
        { echo "ERROR: Group '$SERVICE_GROUP' does not exist." >&2; exit 1; }
}

verify_install_target() {
    if [[ -e "$BASE_DIR" ]]; then
        echo "ERROR: Install directory '$BASE_DIR' already exists." >&2
        exit 1
    fi
}

create_directories() {
    install -d -o root -g root -m 0755 \
        "$BASE_DIR" \
        "$BASE_DIR/web" \
        "$BASE_DIR/web/static" \
        "$BASE_DIR/venv" \
        "$BASE_DIR/scripts"

    install -d -o root -g "$SERVICE_GROUP" -m 0750 \
        "$BASE_DIR/etc"

    install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0750 \
        "$BASE_DIR/data" \
        "$BASE_DIR/run"
}

install_application() {
    install -o root -g root -m 0644 \
        "$REPO_DIR/web/server.py" \
        "$BASE_DIR/web/server.py"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/static/index.html" \
        "$BASE_DIR/web/static/index.html"
}

create_virtualenv() {
    python3 -m venv "$BASE_DIR/venv"

    "$BASE_DIR/venv/bin/python" -m pip install --upgrade pip

    if [[ -f "$REPO_DIR/requirements.txt" ]]; then
        "$BASE_DIR/venv/bin/pip" install \
            --requirement "$REPO_DIR/requirements.txt"
    fi
}

install_systemd_service() {
    install -o root -g root -m 0644 \
        "$REPO_DIR/systemd/xmr.service" \
        "$SERVICE_FILE"

    systemctl daemon-reload
}

main() {
    require_root
    verify_service_account
    verify_install_target

    step "Creating installation directories"
    create_directories

    step "Installing application"
    install_application

    step "Creating Python virtual environment"
    create_virtualenv

    step "Installing systemd service"
    install_systemd_service

    echo
    echo "Bear and Moose XMR installed successfully!"
}

main "$@"
