#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly OPS_DIR="/opt/xmr_ops"
readonly SERVICE_NAME="xmr.service"
readonly SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
readonly ADMIN_SERVICE_NAME="xmr-admin.service"
readonly ADMIN_SERVICE_FILE="/etc/systemd/system/$ADMIN_SERVICE_NAME"
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
    systemctl disable --now "$ADMIN_SERVICE_NAME" 2>/dev/null || true

    rm -f -- "$SERVICE_FILE"
    rm -f -- "$ADMIN_SERVICE_FILE"
    systemctl daemon-reload
    systemctl reset-failed "$SERVICE_NAME" 2>/dev/null || true
    systemctl reset-failed "$ADMIN_SERVICE_NAME" 2>/dev/null || true
}

reset_database() {
    # Installations that failed before MariaDB setup have nothing to reset.
    if ! command -v mariadb >/dev/null 2>&1; then
        return
    fi

    if [[ "$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')" == "1" ]]; then
        step "Switching replica MariaDB to read/write"
        mariadb -e 'STOP SLAVE' 2>/dev/null || true
        mariadb -e 'RESET SLAVE ALL'
        mariadb -e 'SET GLOBAL read_only=OFF'
        [[ "$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')" == "0" ]] || {
            echo "ERROR: MariaDB is still read-only." >&2
            exit 1
        }
    fi

    step "Removing database"
    if ! mariadb -e '
        DROP TABLE IF EXISTS xmr.pools;
        DROP TABLE IF EXISTS xmr.pool_port_sequence;
        DROP TABLE IF EXISTS xmr.sessions;
        DROP TABLE IF EXISTS xmr.users;
    '; then
        echo "WARNING: Application schema could not be removed; continuing reset." >&2
    fi
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

    step "Removing installation directories ($BASE_DIR and $OPS_DIR)"
    remove_installation
    rm -rf -- "$OPS_DIR"

    echo
    echo "Bear and Moose XMR installation removed successfully!"
}

main "$@"
