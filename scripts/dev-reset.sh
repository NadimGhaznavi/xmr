#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SERVICE_NAME="xmr.service"
readonly SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

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

remove_installation() {
    rm -rf -- "$BASE_DIR"
}

main() {
    require_root

    step "Removing systemd service"
    remove_systemd_service

    step "Removing installation directory ($BASE_DIR)"
    remove_installation

    echo
    echo "Bear and Moose XMR installation removed successfully!"
}

main "$@"
