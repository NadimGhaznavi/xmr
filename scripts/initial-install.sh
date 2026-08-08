#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly SERVICE_USER="xmr"
readonly SERVICE_GROUP="xmr"
readonly SERVICE_NAME="xmr.service"
readonly SERVICE_FILE="/etc/systemd/system/xmr.service"
readonly CADDY_CONFIG_DIR="/etc/caddy"
readonly CADDY_FILE="$CADDY_CONFIG_DIR/Caddyfile"
readonly CADDY_BACKUP="$BASE_DIR/etc/Caddyfile.before-xmr"
readonly CADDY_ACTIVE_MARKER="$BASE_DIR/etc/caddy-was-active"
readonly ENV_FILE="$BASE_DIR/etc/xmr.env"
readonly REPLICATION_CREDENTIAL_FILE="/root/.xmr"
readonly REPLICATION_USER="replication_user"
DB_PASSWORD=""
REPLICATION_PASSWORD=""
CLUSTER_ROLE=""

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

install_system_dependencies() {
    if command -v mariadb_config >/dev/null 2>&1 && \
        command -v cc >/dev/null 2>&1 && \
        python3 -c 'import pathlib, sysconfig; assert (pathlib.Path(sysconfig.get_path("include")) / "Python.h").is_file()' \
            >/dev/null 2>&1; then
        return
    fi

    if ! command -v apt-get >/dev/null 2>&1; then
        echo "ERROR: MariaDB Connector/C and a C compiler are required." >&2
        echo "Install your distribution's MariaDB development, compiler," >&2
        echo "and Python development packages, then run this script again." >&2
        exit 1
    fi

    step "Installing MariaDB connector build dependencies"
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        libmariadb-dev \
        python3-dev

    command -v mariadb_config >/dev/null 2>&1 ||
        { echo "ERROR: libmariadb-dev did not provide mariadb_config." >&2; exit 1; }

    python3 -c 'import pathlib, sysconfig; assert (pathlib.Path(sysconfig.get_path("include")) / "Python.h").is_file()' \
        >/dev/null 2>&1 ||
        { echo "ERROR: python3-dev did not provide Python.h." >&2; exit 1; }
}

prompt_db_password() {
    local confirmation=""

    # Do not expose the password if the script was invoked with shell tracing.
    set +x

    while true; do
        printf 'MariaDB password for user %s: ' "$SERVICE_USER" >&2
        if ! IFS= read -r -s DB_PASSWORD; then
            printf '\nERROR: Unable to read the database password.\n' >&2
            exit 1
        fi
        printf '\n' >&2

        if [[ -z "$DB_PASSWORD" ]]; then
            echo "ERROR: The database password cannot be empty." >&2
            continue
        fi

        printf 'Confirm MariaDB password: ' >&2
        if ! IFS= read -r -s confirmation; then
            printf '\nERROR: Unable to read the password confirmation.\n' >&2
            exit 1
        fi
        printf '\n' >&2

        if [[ "$DB_PASSWORD" == "$confirmation" ]]; then
            break
        fi

        DB_PASSWORD=""
        confirmation=""
        echo "ERROR: Passwords do not match; please try again." >&2
    done
}

prompt_replication_password() {
    local confirmation=""

    # Do not expose the password if the script was invoked with shell tracing.
    set +x

    while true; do
        printf 'MariaDB replication password for user %s: ' "$REPLICATION_USER" >&2
        if ! IFS= read -r -s REPLICATION_PASSWORD; then
            printf '\nERROR: Unable to read the replication password.\n' >&2
            exit 1
        fi
        printf '\n' >&2

        if [[ -z "$REPLICATION_PASSWORD" ]]; then
            echo "ERROR: The replication password cannot be empty." >&2
            continue
        fi

        printf 'Confirm MariaDB replication password: ' >&2
        if ! IFS= read -r -s confirmation; then
            printf '\nERROR: Unable to read the replication password confirmation.\n' >&2
            exit 1
        fi
        printf '\n' >&2

        if [[ "$REPLICATION_PASSWORD" == "$confirmation" ]]; then
            break
        fi

        REPLICATION_PASSWORD=""
        confirmation=""
        echo "ERROR: Passwords do not match; please try again." >&2
    done
}

prompt_cluster_role() {
    while true; do
        read -r -p "Cluster role for this node (hot/cold): " CLUSTER_ROLE
        case "$CLUSTER_ROLE" in
            hot|cold) return ;;
            *) echo "ERROR: Role must be 'hot' or 'cold'." >&2 ;;
        esac
    done
}

load_existing_credentials() {
    [[ -f "$REPLICATION_CREDENTIAL_FILE" ]] || return 1
    [[ "$(stat -c '%U:%G:%a' "$REPLICATION_CREDENTIAL_FILE")" == "root:root:600" ]] || {
        echo "ERROR: $REPLICATION_CREDENTIAL_FILE must be owned by root:root with mode 0600." >&2
        return 1
    }

    local answer line key value db_user="" replication_user=""
    read -r -p "Use credentials from $REPLICATION_CREDENTIAL_FILE? (y/N): " answer
    [[ "$answer" =~ ^[Yy]$ ]] || return 1

    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
        [[ "$line" == *=* ]] || {
            echo "ERROR: Invalid entry in $REPLICATION_CREDENTIAL_FILE." >&2
            return 1
        }
        key="${line%%=*}"
        value="${line#*=}"
        case "$key" in
            XMR_DB_USER) db_user="$value" ;;
            XMR_DB_PASSWORD) DB_PASSWORD="$value" ;;
            XMR_REPLICATION_USER) replication_user="$value" ;;
            XMR_REPLICATION_PASSWORD) REPLICATION_PASSWORD="$value" ;;
            *)
                echo "ERROR: Unknown setting in $REPLICATION_CREDENTIAL_FILE: $key" >&2
                return 1
                ;;
        esac
    done <"$REPLICATION_CREDENTIAL_FILE"

    [[ -z "$db_user" || "$db_user" == "$SERVICE_USER" ]] || {
        echo "ERROR: Unexpected database user in $REPLICATION_CREDENTIAL_FILE." >&2
        return 1
    }
    [[ "$replication_user" == "$REPLICATION_USER" ]] || {
        echo "ERROR: Unexpected replication user in $REPLICATION_CREDENTIAL_FILE." >&2
        return 1
    }
    [[ -n "$REPLICATION_PASSWORD" ]] || {
        echo "ERROR: Replication password missing from $REPLICATION_CREDENTIAL_FILE." >&2
        return 1
    }
    [[ -n "$DB_PASSWORD" ]] || DB_PASSWORD="$REPLICATION_PASSWORD"
    echo "Using credentials from $REPLICATION_CREDENTIAL_FILE."
}

create_directories() {
    install -d -o root -g root -m 0755 \
        "$BASE_DIR" \
        "$BASE_DIR/constants" \
        "$BASE_DIR/db" \
        "$BASE_DIR/mgr" \
        "$BASE_DIR/web" \
        "$BASE_DIR/web/static" \
        "$BASE_DIR/web/static/img" \
        "$BASE_DIR/web/templates" \
        "$BASE_DIR/venv"

    install -d -o root -g "$SERVICE_GROUP" -m 0750 \
        "$BASE_DIR/etc"

    install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0750 \
        "$BASE_DIR/data" \
        "$BASE_DIR/run"
}

install_application() {
    install -o root -g root -m 0644 \
        "$REPO_DIR/requirements.txt" \
        "$BASE_DIR/requirements.txt"

    install -o root -g root -m 0644 \
        "$REPO_DIR/constants/DDefaults.py" \
        "$BASE_DIR/constants/DDefaults.py"

    install -o root -g root -m 0644 \
        "$REPO_DIR/db/__init__.py" \
        "$REPO_DIR/db/AppDb.py" \
        "$REPO_DIR/db/DbMgr.py" \
        "$REPO_DIR/db/SessDb.py" \
        "$REPO_DIR/db/XmrDb.py" \
        "$BASE_DIR/db/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/mgr/__init__.py" \
        "$REPO_DIR/mgr/AppMgr.py" \
        "$REPO_DIR/mgr/AcctMgr.py" \
        "$REPO_DIR/mgr/SessMgr.py" \
        "$BASE_DIR/mgr/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/__init__.py" \
        "$REPO_DIR/web/Interface.py" \
        "$REPO_DIR/web/server.py" \
        "$REPO_DIR/web/session_middleware.py" \
        "$BASE_DIR/web/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/templates/base.html" \
        "$REPO_DIR/web/templates/login.html" \
        "$REPO_DIR/web/templates/signup.html" \
        "$BASE_DIR/web/templates/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/static/index.html" \
        "$BASE_DIR/web/static/index.html"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/static/img/logo.png" \
        "$BASE_DIR/web/static/img/logo.png"
}

create_environment_file() {
    local escaped_password="$DB_PASSWORD"
    escaped_password=${escaped_password//\\/\\\\}
    escaped_password=${escaped_password//\"/\\\"}

    install -o root -g "$SERVICE_GROUP" -m 0640 /dev/null "$ENV_FILE"
    printf '%s\n' \
        'XMR_DB_HOST=localhost' \
        'XMR_DB_PORT=3306' \
        'XMR_DB_NAME=xmr' \
        'XMR_DB_USER=xmr' \
        'XMR_P2POOL_PORT_MIN=20000' \
        'XMR_P2POOL_PORT_MAX=29999' >"$ENV_FILE"
    printf 'XMR_DB_PASSWORD="%s"\n' "$escaped_password" >>"$ENV_FILE"

    escaped_password=""
}

create_replication_credential_file() {
    install -o root -g root -m 0600 /dev/null "$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_DB_USER=%s\n' "$SERVICE_USER" \
        >"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_DB_PASSWORD=%s\n' "$DB_PASSWORD" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_REPLICATION_USER=%s\n' "$REPLICATION_USER" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_REPLICATION_PASSWORD=%s\n' "$REPLICATION_PASSWORD" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    REPLICATION_PASSWORD=""
}

create_virtualenv() {
    python3 -m venv "$BASE_DIR/venv"

    "$BASE_DIR/venv/bin/python" -m pip install --upgrade pip

    if [[ -f "$REPO_DIR/requirements.txt" ]]; then
        "$BASE_DIR/venv/bin/pip" install \
            --requirement "$REPO_DIR/requirements.txt"
    fi
}

initialize_database() {
    mariadb -e 'SET GLOBAL read_only=OFF'
    (
        cd "$BASE_DIR"
        XMR_DB_PASSWORD="$DB_PASSWORD" "$BASE_DIR/venv/bin/python" -c \
            'from db.AppDb import AppDb; from db.SessDb import SessDb; AppDb().initialize_schema(); SessDb().initialize_schema()'
    )
    DB_PASSWORD=""
}

configure_cluster_role() {
    if [[ "$CLUSTER_ROLE" == "hot" ]]; then
        systemctl enable --now "$SERVICE_NAME"
        systemctl is-active --quiet "$SERVICE_NAME" || {
            echo "ERROR: $SERVICE_NAME failed to start." >&2
            exit 1
        }
        echo "Configured $(hostname -s) as the hot node."
        return
    fi

    local node
    node=$(hostname -s)
    printf 'demote %s\n' "$node" | "$REPO_DIR/scripts/cluster-mgr.sh" demote
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

    caddy fmt --overwrite "$CADDY_FILE"
    caddy validate --config "$CADDY_FILE"
    systemctl reload-or-restart caddy.service
}

main() {
    require_root
    verify_service_account
    verify_install_target
    verify_dependencies
    install_system_dependencies
    prompt_cluster_role
    if ! load_existing_credentials; then
        prompt_db_password
        prompt_replication_password
    fi

    step "Creating installation directories"
    create_directories

    step "Installing application"
    install_application

    step "Creating private environment file"
    create_environment_file

    step "Creating private replication credential file"
    create_replication_credential_file

    step "Creating Python virtual environment"
    create_virtualenv

    step "Initializing database schema"
    initialize_database

    step "Installing systemd service"
    install_systemd_service

    step "Configuring $CLUSTER_ROLE cluster role"
    configure_cluster_role

    step "Installing Caddy configuration"
    install_caddy_config

    echo
    echo "Bear and Moose XMR installed successfully!"
}

main "$@"
