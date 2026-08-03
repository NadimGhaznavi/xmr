#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SERVICE_NAME="xmr.service"
readonly SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
readonly CADDY_FILE="/etc/caddy/Caddyfile"
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

remove_systemd_service() {
    # Stop the service before removing the files it may be using. Disabling it
    # also removes any symlinks created after the initial installation.
    systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true

    rm -f -- "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true
}

reset_database() {
    local python="$BASE_DIR/venv/bin/python"
    local database_module="$BASE_DIR/web/xmrdb.py"
    local environment_file="$BASE_DIR/etc/xmr.env"

    # Installations that failed before database initialization have nothing to
    # reset and may not contain a usable MariaDB connector.
    if [[ ! -x "$python" || ! -f "$database_module" || ! -f "$environment_file" ]]; then
        return
    fi
    if ! "$python" -c 'import mariadb' >/dev/null 2>&1; then
        step "Removing database failed"
        return
    fi

    step "Removing database"
    "$python" "$database_module" reset --env-file "$environment_file"
}

restore_caddy_config() {
    if [[ -f "$CADDY_BACKUP" ]]; then
        install -o root -g root -m 0644 "$CADDY_BACKUP" "$CADDY_FILE"
    else
        rm -f -- "$CADDY_FILE"
    fi

    if [[ -f "$CADDY_ACTIVE_MARKER" ]]; then
        systemctl reload-or-restart caddy.service
    else
        systemctl stop caddy.service 2>/dev/null || true
    fi
}

remove_installation() {
    rm -rf -- "$BASE_DIR"
}

main() {
    require_root

    step "Removing systemd service"
    remove_systemd_service

    step "Removing application database schema"
    reset_database

    step "Restoring Caddy configuration"
    restore_caddy_config

    step "Removing installation directory ($BASE_DIR)"
    remove_installation

    echo
    echo "Bear and Moose XMR installation removed successfully!"
}

main "$@"
