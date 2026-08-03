#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly SERVICE_USER="xmr"
readonly SERVICE_GROUP="xmr"
readonly SERVICE_FILE="/etc/systemd/system/xmr.service"
readonly CADDY_CONFIG_DIR="/etc/caddy"
readonly CADDY_FILE="$CADDY_CONFIG_DIR/Caddyfile"
readonly CADDY_BACKUP="$BASE_DIR/etc/Caddyfile.before-xmr"
readonly CADDY_ACTIVE_MARKER="$BASE_DIR/etc/caddy-was-active"

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

verify_dependencies() {
    command -v python3 >/dev/null 2>&1 ||
        { echo "ERROR: python3 is not installed." >&2; exit 1; }

    command -v caddy >/dev/null 2>&1 ||
        { echo "ERROR: Caddy is not installed." >&2; exit 1; }
}

create_directories() {
    install -d -o root -g root -m 0755 \
        "$BASE_DIR" \
        "$BASE_DIR/web" \
        "$BASE_DIR/web/static" \
        "$BASE_DIR/web/static/img" \
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

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/static/img/logo.png" \
        "$BASE_DIR/web/static/img/logo.png"
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

install_caddy_config() {
    install -d -o root -g root -m 0755 "$CADDY_CONFIG_DIR"

    if [[ -f "$CADDY_FILE" ]]; then
        install -o root -g root -m 0644 "$CADDY_FILE" "$CADDY_BACKUP"
    fi

    if systemctl is-active --quiet caddy.service; then
        install -o root -g root -m 0600 /dev/null "$CADDY_ACTIVE_MARKER"
    fi

    install -o root -g root -m 0644 \
        "$REPO_DIR/systemd/Caddyfile" \
        "$CADDY_FILE"

    caddy validate --config "$CADDY_FILE"
    systemctl reload-or-restart caddy.service
}

main() {
    require_root
    verify_service_account
    verify_install_target
    verify_dependencies

    step "Creating installation directories"
    create_directories

    step "Installing application"
    install_application

    step "Creating Python virtual environment"
    create_virtualenv

    step "Installing systemd service"
    install_systemd_service

    step "Installing Caddy configuration"
    install_caddy_config

    echo
    echo "Bear and Moose XMR installed successfully!"
}

main "$@"
