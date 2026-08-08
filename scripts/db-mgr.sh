#!/bin/bash
set -euo pipefail

readonly CREDENTIAL_FILE="/root/.xmr"
readonly NODES=(bama wintermute)
readonly SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)

XMR_REPLICATION_USER=""
XMR_REPLICATION_PASSWORD=""

usage() {
    echo "Usage:" >&2
    echo "  $0 role" >&2
    echo "  $0 replication" >&2
    echo "  $0 replica-healthy" >&2
    echo "  $0 replica-caught-up" >&2
    echo "  $0 set-read-only" >&2
    echo "  $0 promote" >&2
    echo "  $0 demote-to <bama|wintermute>" >&2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

valid_node() {
    [[ "$1" == "bama" || "$1" == "wintermute" ]]
}

require_root() {
    [[ $EUID -eq 0 ]] || fail "This command must be run as root"
}

load_replication_credentials() {
    [[ -f "$CREDENTIAL_FILE" ]] || fail "Missing $CREDENTIAL_FILE"
    [[ "$(stat -c '%U:%G:%a' "$CREDENTIAL_FILE")" == "root:root:600" ]] ||
        fail "$CREDENTIAL_FILE must be owned by root:root with mode 0600"

    local line key value
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
        [[ "$line" == *=* ]] || fail "Invalid entry in $CREDENTIAL_FILE"
        key="${line%%=*}"
        value="${line#*=}"
        case "$key" in
            XMR_DB_USER|XMR_DB_PASSWORD) ;;
            XMR_REPLICATION_USER) XMR_REPLICATION_USER="$value" ;;
            XMR_REPLICATION_PASSWORD) XMR_REPLICATION_PASSWORD="$value" ;;
            *) fail "Unknown setting in $CREDENTIAL_FILE: $key" ;;
        esac
    done <"$CREDENTIAL_FILE"

    [[ "$XMR_REPLICATION_USER" =~ ^[A-Za-z0-9_]+$ ]] ||
        fail "Invalid replication user in $CREDENTIAL_FILE"
    [[ -n "$XMR_REPLICATION_PASSWORD" ]] ||
        fail "Missing replication password in $CREDENTIAL_FILE"
}

sql_string() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\'/\'\'}
    printf "'%s'" "$value"
}

slave_status() {
    mariadb -e 'SHOW SLAVE STATUS\G'
}

role() {
    local read_only
    read_only=$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')
    [[ "$read_only" == "0" ]] && echo primary || echo replica
}

replication() {
    local output lag
    output=$(slave_status 2>/dev/null || true)
    if [[ -z "$output" ]]; then
        echo n/a
    elif grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
         grep -q 'Slave_SQL_Running: Yes' <<<"$output"; then
        lag=$(sed -n 's/^[[:space:]]*Seconds_Behind_Master: //p' <<<"$output")
        echo "healthy, ${lag:-unknown}s lag"
    else
        echo unhealthy
    fi
}

replica_healthy() {
    local output
    output=$(slave_status)
    grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
        grep -q 'Slave_SQL_Running: Yes' <<<"$output"
}

replica_caught_up() {
    local output
    output=$(slave_status)
    grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
        grep -q 'Slave_SQL_Running: Yes' <<<"$output" &&
        grep -q 'Seconds_Behind_Master: 0' <<<"$output"
}

set_read_only() {
    require_root
    mariadb -e 'SET GLOBAL read_only=ON'
    [[ "$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')" == "1" ]] ||
        fail "MariaDB is not read-only"
}

promote() {
    require_root
    mariadb -e 'STOP SLAVE' 2>/dev/null || true
    mariadb -e 'RESET SLAVE ALL'
    mariadb -e 'SET GLOBAL read_only=OFF'
    [[ "$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')" == "0" ]] ||
        fail "MariaDB is still read-only"
}

demote_to() {
    local primary=$1
    valid_node "$primary" || fail "Unknown primary node: $primary"
    require_root
    load_replication_credentials

    local user_sql password_sql primary_position output
    user_sql=$(sql_string "$XMR_REPLICATION_USER")
    password_sql=$(sql_string "$XMR_REPLICATION_PASSWORD")
    primary_position=$(ssh "${SSH_OPTIONS[@]}" "root@$primary" \
        "mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.gtid_current_pos'")
    [[ "$primary_position" =~ ^[0-9]+-[0-9]+-[0-9]+(,[0-9]+-[0-9]+-[0-9]+)*$ ]] ||
        fail "Unable to determine the GTID position on $primary"

    set_read_only
    mariadb -e 'STOP SLAVE' 2>/dev/null || true
    mariadb -e 'RESET SLAVE ALL'
    mariadb -e "SET GLOBAL gtid_slave_pos='$primary_position'"
    mariadb -e "
        CHANGE MASTER TO
            MASTER_HOST='$primary',
            MASTER_USER=$user_sql,
            MASTER_PASSWORD=$password_sql,
            MASTER_USE_GTID=slave_pos,
            MASTER_SSL=1,
            MASTER_SSL_VERIFY_SERVER_CERT=1;
        START SLAVE;
    "

    for _ in {1..10}; do
        output=$(slave_status)
        if grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
           grep -q 'Slave_SQL_Running: Yes' <<<"$output"; then
            echo "MariaDB is replicating from $primary."
            return
        fi
        sleep 1
    done
    sed -n \
        -e '/Slave_IO_Running:/p' \
        -e '/Slave_SQL_Running:/p' \
        -e '/Last_IO_Error:/p' \
        -e '/Last_SQL_Error:/p' <<<"$output" >&2
    fail "MariaDB replication did not start"
}

[[ $# -ge 1 ]] || { usage; exit 1; }

case "$1" in
    role) [[ $# -eq 1 ]] || { usage; exit 1; }; role ;;
    replication) [[ $# -eq 1 ]] || { usage; exit 1; }; replication ;;
    replica-healthy) [[ $# -eq 1 ]] || { usage; exit 1; }; replica_healthy ;;
    replica-caught-up) [[ $# -eq 1 ]] || { usage; exit 1; }; replica_caught_up ;;
    set-read-only) [[ $# -eq 1 ]] || { usage; exit 1; }; set_read_only ;;
    promote) [[ $# -eq 1 ]] || { usage; exit 1; }; promote ;;
    demote-to) [[ $# -eq 2 ]] || { usage; exit 1; }; demote_to "$2" ;;
    *) usage; exit 1 ;;
esac
