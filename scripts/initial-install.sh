#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly SERVICE_USER="xmr"
readonly SERVICE_GROUP="xmr"
readonly SERVICE_NAME="xmr.service"
readonly SERVICE_FILE="/etc/systemd/system/xmr.service"
readonly ADMIN_SERVICE_USER="xmr-admin"
readonly ADMIN_SERVICE_GROUP="xmr-admin"
readonly ADMIN_SERVICE_NAME="xmr-admin.service"
readonly ADMIN_SERVICE_FILE="/etc/systemd/system/xmr-admin.service"
readonly CADDY_CONFIG_DIR="/etc/caddy"
readonly CADDY_FILE="$CADDY_CONFIG_DIR/Caddyfile"
readonly CADDY_BACKUP="$BASE_DIR/etc/Caddyfile.before-xmr"
readonly CADDY_ACTIVE_MARKER="$BASE_DIR/etc/caddy-was-active"
readonly ENV_FILE="$BASE_DIR/etc/xmr.env"
readonly ADMIN_ENV_FILE="$BASE_DIR/etc/xmr-admin.env"
readonly REPLICATION_CREDENTIAL_FILE="/root/.xmr"
readonly REPLICATION_USER="replication_user"
DB_PASSWORD=""
ADMIN_DB_USER="xmradmin"
ADMIN_DB_PASSWORD=""
ADMIN_WEB_PASSWORD=""
REPLICATION_PASSWORD=""
SESSION_SECRET=""
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

ensure_service_account() {
    if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
        groupadd --system "$SERVICE_GROUP"
    fi

    if ! id "$SERVICE_USER" >/dev/null 2>&1; then
        useradd --system \
            --gid "$SERVICE_GROUP" \
            --home-dir /nonexistent \
            --shell /usr/sbin/nologin \
            "$SERVICE_USER"
    fi

    if ! getent group "$ADMIN_SERVICE_GROUP" >/dev/null 2>&1; then
        groupadd --system "$ADMIN_SERVICE_GROUP"
    fi
    if ! id "$ADMIN_SERVICE_USER" >/dev/null 2>&1; then
        useradd --system \
            --gid "$ADMIN_SERVICE_GROUP" \
            --home-dir /nonexistent \
            --shell /usr/sbin/nologin \
            "$ADMIN_SERVICE_USER"
    fi
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

    command -v apt-get >/dev/null 2>&1 ||
        { echo "ERROR: apt-get is required to install dependencies." >&2; exit 1; }
}

install_system_dependencies() {
    if command -v caddy >/dev/null 2>&1 && \
        command -v mariadb >/dev/null 2>&1 && \
        command -v mariadb_config >/dev/null 2>&1 && \
        command -v cc >/dev/null 2>&1 && \
        python3 -c 'import pathlib, sysconfig; assert (pathlib.Path(sysconfig.get_path("include")) / "Python.h").is_file()' \
            >/dev/null 2>&1; then
        return
    fi

    step "Installing system dependencies"
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        caddy \
        libmariadb-dev \
        mariadb-client \
        mariadb-server \
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

prompt_admin_password() {
    local confirmation=""

    set +x
    while true; do
        printf 'MariaDB password for admin service user %s: ' "$ADMIN_DB_USER" >&2
        IFS= read -r -s ADMIN_DB_PASSWORD || exit 1
        printf '\n' >&2
        if [[ -z "$ADMIN_DB_PASSWORD" ]]; then
            echo "ERROR: The admin database password cannot be empty." >&2
            continue
        fi
        printf 'Confirm admin MariaDB password: ' >&2
        IFS= read -r -s confirmation || exit 1
        printf '\n' >&2
        [[ "$ADMIN_DB_PASSWORD" == "$confirmation" ]] && return
        echo "ERROR: Passwords do not match; please try again." >&2
    done
}

prompt_admin_web_password() {
    local confirmation=""

    set +x
    while true; do
        printf 'Browser password for admin user %s: ' "$ADMIN_DB_USER" >&2
        IFS= read -r -s ADMIN_WEB_PASSWORD || exit 1
        printf '\n' >&2
        if [[ ${#ADMIN_WEB_PASSWORD} -lt 16 ]]; then
            echo "ERROR: The admin browser password must have at least 16 characters." >&2
            continue
        fi
        if [[ "$ADMIN_WEB_PASSWORD" == "$ADMIN_DB_PASSWORD" ]]; then
            echo "ERROR: The browser and database passwords must be different." >&2
            continue
        fi
        printf 'Confirm admin browser password: ' >&2
        IFS= read -r -s confirmation || exit 1
        printf '\n' >&2
        [[ "$ADMIN_WEB_PASSWORD" == "$confirmation" ]] && return
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

    local answer line key value db_user="" replication_user="" admin_user=""
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
            XMR_ADMIN_USER) admin_user="$value" ;;
            XMR_ADMIN_PASSWORD) ADMIN_DB_PASSWORD="$value" ;;
            XMR_ADMIN_WEB_PASSWORD) ADMIN_WEB_PASSWORD="$value" ;;
            XMR_SESSION_SECRET) SESSION_SECRET="$value" ;;
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
    [[ "$admin_user" =~ ^[A-Za-z0-9_]+$ ]] || {
        echo "ERROR: Invalid or missing XMR_ADMIN_USER." >&2
        return 1
    }
    [[ "$admin_user" != "root" && "$admin_user" != "$SERVICE_USER" && \
       "$admin_user" != "$REPLICATION_USER" ]] || {
        echo "ERROR: XMR_ADMIN_USER must identify a separate service account." >&2
        return 1
    }
    [[ -n "$ADMIN_DB_PASSWORD" ]] || {
        echo "ERROR: XMR_ADMIN_PASSWORD is missing." >&2
        return 1
    }
    if [[ -n "$ADMIN_WEB_PASSWORD" && ${#ADMIN_WEB_PASSWORD} -lt 16 ]]; then
        echo "WARNING: XMR_ADMIN_WEB_PASSWORD must have at least 16 characters." >&2
        ADMIN_WEB_PASSWORD=""
    fi
    if [[ -n "$ADMIN_WEB_PASSWORD" && \
          "$ADMIN_WEB_PASSWORD" == "$ADMIN_DB_PASSWORD" ]]; then
        echo "WARNING: Admin browser and database passwords must be different." >&2
        ADMIN_WEB_PASSWORD=""
    fi
    ADMIN_DB_USER="$admin_user"
    if [[ -n "$SESSION_SECRET" && ! "$SESSION_SECRET" =~ ^[0-9a-f]{64}$ ]]; then
        echo "ERROR: XMR_SESSION_SECRET must contain 64 lowercase hex characters." >&2
        return 1
    fi
    echo "Using credentials from $REPLICATION_CREDENTIAL_FILE."
}

create_directories() {
    install -d -o root -g root -m 0755 \
        "$BASE_DIR" \
        "$BASE_DIR/constants" \
        "$BASE_DIR/admin" \
        "$BASE_DIR/admin/templates" \
        "$BASE_DIR/db" \
        "$BASE_DIR/mgr" \
        "$BASE_DIR/web" \
        "$BASE_DIR/web/static" \
        "$BASE_DIR/web/static/img" \
        "$BASE_DIR/web/templates" \
        "$BASE_DIR/venv"

    install -d -o root -g root -m 0751 \
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
        "$REPO_DIR/constants/__init__.py" \
        "$REPO_DIR/constants/DDefaults.py" \
        "$BASE_DIR/constants/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/db/__init__.py" \
        "$REPO_DIR/db/AdminDb.py" \
        "$REPO_DIR/db/AppDb.py" \
        "$REPO_DIR/db/DbMgr.py" \
        "$REPO_DIR/db/PoolDb.py" \
        "$REPO_DIR/db/SessDb.py" \
        "$REPO_DIR/db/XmrDb.py" \
        "$BASE_DIR/db/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/mgr/__init__.py" \
        "$REPO_DIR/mgr/AdminMgr.py" \
        "$REPO_DIR/mgr/AppMgr.py" \
        "$REPO_DIR/mgr/AcctMgr.py" \
        "$REPO_DIR/mgr/PoolMgr.py" \
        "$REPO_DIR/mgr/SessMgr.py" \
        "$BASE_DIR/mgr/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/__init__.py" \
        "$REPO_DIR/web/Interface.py" \
        "$REPO_DIR/web/Server.py" \
        "$REPO_DIR/web/UserSession.py" \
        "$REPO_DIR/web/server.py" \
        "$REPO_DIR/web/session_middleware.py" \
        "$BASE_DIR/web/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/admin/__init__.py" \
        "$REPO_DIR/admin/server.py" \
        "$BASE_DIR/admin/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/admin/templates/base.html" \
        "$REPO_DIR/admin/templates/accounts.html" \
        "$REPO_DIR/admin/templates/edit-account.html" \
        "$REPO_DIR/admin/templates/cold.html" \
        "$BASE_DIR/admin/templates/"

    install -o root -g root -m 0644 \
        "$REPO_DIR/web/templates/base.html" \
        "$REPO_DIR/web/templates/dashboard.html" \
        "$REPO_DIR/web/templates/login.html" \
        "$REPO_DIR/web/templates/new-pool.html" \
        "$REPO_DIR/web/templates/edit-pool.html" \
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
    local escaped_admin_password="$ADMIN_DB_PASSWORD"
    local admin_web_hash
    escaped_password=${escaped_password//\\/\\\\}
    escaped_password=${escaped_password//\"/\\\"}

    install -o root -g "$SERVICE_GROUP" -m 0640 /dev/null "$ENV_FILE"
    printf '%s\n' \
        'XMR_DB_HOST=localhost' \
        'XMR_DB_PORT=3306' \
        'XMR_DB_NAME=xmr' \
        'XMR_DB_USER=xmr' \
        "XMR_SESSION_SECRET=$SESSION_SECRET" \
        'XMR_P2POOL_PORT_MIN=20000' \
        'XMR_P2POOL_PORT_MAX=29999' >"$ENV_FILE"
    printf 'XMR_DB_PASSWORD="%s"\n' "$escaped_password" >>"$ENV_FILE"

    escaped_password=""

    escaped_admin_password=${escaped_admin_password//\\/\\\\}
    escaped_admin_password=${escaped_admin_password//\"/\\\"}
    admin_web_hash=$(printf '%s' "$ADMIN_WEB_PASSWORD" | python3 -c '
import base64
import hashlib
import secrets
import sys

password = sys.stdin.buffer.read()
salt = secrets.token_bytes(16)
digest = hashlib.scrypt(password, salt=salt, n=16384, r=8, p=1, dklen=32)
encode = lambda value: base64.b64encode(value).decode("ascii")
print(f"scrypt$16384$8$1${encode(salt)}${encode(digest)}")
')
    install -o root -g "$ADMIN_SERVICE_GROUP" -m 0640 /dev/null "$ADMIN_ENV_FILE"
    printf '%s\n' \
        'XMR_ADMIN_DB_HOST=localhost' \
        'XMR_ADMIN_DB_PORT=3306' \
        'XMR_ADMIN_DB_NAME=xmr' \
        "XMR_ADMIN_DB_USER=$ADMIN_DB_USER" \
        "XMR_ADMIN_WEB_USER=$ADMIN_DB_USER" \
        "XMR_ADMIN_WEB_PASSWORD_HASH=$admin_web_hash" \
        'XMR_TRUSTED_LAN=192.168.0.0/24' >"$ADMIN_ENV_FILE"
    printf 'XMR_ADMIN_DB_PASSWORD="%s"\n' "$escaped_admin_password" \
        >>"$ADMIN_ENV_FILE"
    escaped_admin_password=""
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
    printf 'XMR_ADMIN_USER=%s\n' "$ADMIN_DB_USER" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_ADMIN_PASSWORD=%s\n' "$ADMIN_DB_PASSWORD" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_ADMIN_WEB_PASSWORD=%s\n' "$ADMIN_WEB_PASSWORD" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    printf 'XMR_SESSION_SECRET=%s\n' "$SESSION_SECRET" \
        >>"$REPLICATION_CREDENTIAL_FILE"
    ADMIN_WEB_PASSWORD=""
}

create_virtualenv() {
    python3 -m venv "$BASE_DIR/venv"

    "$BASE_DIR/venv/bin/python" -m pip install --upgrade pip

    if [[ -f "$REPO_DIR/requirements.txt" ]]; then
        "$BASE_DIR/venv/bin/pip" install \
            --requirement "$REPO_DIR/requirements.txt"
    fi
}

sql_string() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\'/\'\'}
    printf "'%s'" "$value"
}

provision_database() {
    local db_password_sql replication_password_sql admin_user_sql admin_password_sql
    db_password_sql=$(sql_string "$DB_PASSWORD")
    replication_password_sql=$(sql_string "$REPLICATION_PASSWORD")
    admin_user_sql=$(sql_string "$ADMIN_DB_USER")
    admin_password_sql=$(sql_string "$ADMIN_DB_PASSWORD")

    mariadb -e "
        CREATE DATABASE IF NOT EXISTS xmr
            CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        DROP USER IF EXISTS 'xmr'@'localhost';
        DROP USER IF EXISTS $admin_user_sql@'localhost';
        CREATE USER IF NOT EXISTS 'xmr' IDENTIFIED BY $db_password_sql;
        ALTER USER 'xmr' IDENTIFIED BY $db_password_sql;
        CREATE USER IF NOT EXISTS 'replication_user'
            IDENTIFIED BY $replication_password_sql;
        ALTER USER 'replication_user' IDENTIFIED BY $replication_password_sql;
        CREATE USER IF NOT EXISTS $admin_user_sql IDENTIFIED BY $admin_password_sql;
        ALTER USER $admin_user_sql IDENTIFIED BY $admin_password_sql;
        REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'xmr';
        REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'replication_user';
        REVOKE ALL PRIVILEGES, GRANT OPTION FROM $admin_user_sql;
        GRANT REPLICATION SLAVE ON *.* TO 'replication_user';
        FLUSH PRIVILEGES;
    "
}

initialize_database() {
    mariadb -e 'SET GLOBAL read_only=OFF'
    provision_database
    (
        cd "$BASE_DIR"
        "$BASE_DIR/venv/bin/python" -c \
            'from db.AppDb import _USERS_SCHEMA; from db.SessDb import _SESSION_SCHEMA; from db.PoolDb import _POOL_SCHEMA; print(_USERS_SCHEMA, ";", _SESSION_SCHEMA, ";", _POOL_SCHEMA, ";")' |
            mariadb xmr
    )
    local admin_user_sql
    admin_user_sql=$(sql_string "$ADMIN_DB_USER")
    mariadb -e "
        GRANT SELECT (id, username, password_hash, wallet_address, role, status,
                      created_at, disabled_at),
              INSERT (username, password_hash, wallet_address, role)
            ON xmr.users TO 'xmr';
        GRANT SELECT (id, token_digest, account_id, authenticated, created_at,
                      last_activity_at, expires_at, absolute_expires_at, revoked_at),
              INSERT (token_digest, authenticated, created_at, last_activity_at,
                      expires_at, absolute_expires_at),
              UPDATE (token_digest, account_id, authenticated, last_activity_at,
                      expires_at, revoked_at)
            ON xmr.sessions TO 'xmr';
        GRANT SELECT (id, account_id, chain, port, created_at, updated_at),
              INSERT (account_id, chain, port), UPDATE (chain)
            ON xmr.pools TO 'xmr';
        GRANT SELECT (id, next_port), UPDATE (next_port)
            ON xmr.pool_port_sequence TO 'xmr';
        GRANT SELECT (id, username, wallet_address, role, status, created_at,
                      disabled_at)
            ON xmr.users TO $admin_user_sql;
        GRANT UPDATE (username, wallet_address, status, disabled_at)
            ON xmr.users TO $admin_user_sql;
        GRANT SELECT (account_id, revoked_at), UPDATE (revoked_at)
            ON xmr.sessions TO $admin_user_sql;
        FLUSH PRIVILEGES;
        SHOW GRANTS FOR 'xmr';
        SHOW GRANTS FOR 'replication_user';
        SHOW GRANTS FOR $admin_user_sql;
    "
    DB_PASSWORD=""
    ADMIN_DB_PASSWORD=""
    REPLICATION_PASSWORD=""
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

    # This is a newly initialized cold node. Its schema setup created local
    # GTIDs that are not part of the hot node's history. Discard that initial
    # binlog before adopting the hot node's replication position.
    mariadb -e 'STOP SLAVE' 2>/dev/null || true
    mariadb -e 'RESET SLAVE ALL'
    mariadb -e 'RESET MASTER'
    mariadb -e "SET GLOBAL gtid_slave_pos = ''"

    local node
    node=$(hostname -s)
    printf 'demote %s\n' "$node" | "$REPO_DIR/scripts/cluster-mgr.sh" demote
}

install_systemd_service() {
    install -o root -g root -m 0644 \
        "$REPO_DIR/systemd/xmr.service" \
        "$SERVICE_FILE"
    install -o root -g root -m 0644 \
        "$REPO_DIR/systemd/xmr-admin.service" \
        "$ADMIN_SERVICE_FILE"

    systemctl daemon-reload
}

start_admin_service() {
    systemctl enable --now "$ADMIN_SERVICE_NAME"
    systemctl is-active --quiet "$ADMIN_SERVICE_NAME" || {
        echo "ERROR: $ADMIN_SERVICE_NAME failed to start." >&2
        exit 1
    }
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
    ensure_service_account
    verify_install_target
    verify_dependencies
    install_system_dependencies
    prompt_cluster_role
    if ! load_existing_credentials; then
        prompt_db_password
        prompt_replication_password
        prompt_admin_password
    fi
    [[ -n "$ADMIN_WEB_PASSWORD" ]] || prompt_admin_web_password
    if [[ -z "$SESSION_SECRET" ]]; then
        SESSION_SECRET=$(printf '%s' "$DB_PASSWORD" | python3 -c \
            'import hashlib, sys; print(hashlib.sha256(b"xmr-session-v1\0" + sys.stdin.buffer.read()).hexdigest())')
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

    step "Starting LAN admin service"
    start_admin_service

    step "Installing Caddy configuration"
    install_caddy_config

    echo
    echo "Bear and Moose XMR installed successfully!"
}

main "$@"
