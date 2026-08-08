#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SERVICE="xmr.service"
readonly CREDENTIAL_FILE="/root/.xmr"
readonly NODES=(bama wintermute)
readonly SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)
readonly LOCAL_NODE="$(hostname -s)"

XMR_REPLICATION_USER=""
XMR_REPLICATION_PASSWORD=""

usage() {
    echo "Usage:" >&2
    echo "  $0 status" >&2
    echo "  $0 restart" >&2
    echo "  $0 failover-to <bama|wintermute>" >&2
    echo "  $0 promote" >&2
    echo "  $0 demote" >&2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

valid_node() {
    [[ "$1" == "bama" || "$1" == "wintermute" ]]
}

peer_of() {
    [[ "$1" == "bama" ]] && echo wintermute || echo bama
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

remote() {
    local node=$1
    shift
    if [[ "$node" == "$LOCAL_NODE" ]]; then
        [[ $# -eq 1 ]] || fail "Local command must be supplied as one argument"
        bash -c "$1"
        return
    fi
    ssh "${SSH_OPTIONS[@]}" "root@$node" "$@"
}

version_on() {
    remote "$1" "cd '$BASE_DIR' && ./venv/bin/python -c 'from constants.DDefaults import DDef; print(DDef.XMR_VERSION)'"
}

service_on() {
    remote "$1" "systemctl is-active '$SERVICE' 2>/dev/null || true"
}

db_role_on() {
    local read_only
    read_only=$(remote "$1" "mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only'")
    [[ "$read_only" == "0" ]] && echo primary || echo replica
}

replication_on() {
    local output
    output=$(remote "$1" "mariadb -e 'SHOW SLAVE STATUS\\G'" 2>/dev/null || true)
    if [[ -z "$output" ]]; then
        echo n/a
    elif grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
         grep -q 'Slave_SQL_Running: Yes' <<<"$output"; then
        local lag
        lag=$(sed -n 's/^[[:space:]]*Seconds_Behind_Master: //p' <<<"$output")
        echo "healthy, ${lag:-unknown}s lag"
    else
        echo unhealthy
    fi
}

status() {
    local failed=0
    local bama_version=""
    local wintermute_version=""

    printf '%-12s %-10s %-12s %-10s %s\n' "Node" "XMR" "XMR_VERSION" "MariaDB" "Replication"
    for node in "${NODES[@]}"; do
        if ! remote "$node" "true" >/dev/null 2>&1; then
            printf '%-12s %s\n' "$node" "unreachable"
            failed=1
            continue
        fi
        version=$(version_on "$node" 2>/dev/null || echo unreadable)
        service=$(service_on "$node")
        role=$(db_role_on "$node" 2>/dev/null || echo unknown)
        replication=$(replication_on "$node")
        printf '%-12s %-10s %-12s %-10s %s\n' \
            "$node" "$service" "$version" "$role" "$replication"
        [[ "$node" == bama ]] && bama_version="$version" || wintermute_version="$version"
    done

    if [[ -n "$bama_version" && "$bama_version" == "$wintermute_version" ]]; then
        echo "XMR_VERSION: identical ($bama_version)"
    else
        echo "XMR_VERSION: mismatch or unavailable"
        failed=1
    fi
    return "$failed"
}

replica_caught_up() {
    local node=$1
    local output
    output=$(remote "$node" "mariadb -e 'SHOW SLAVE STATUS\\G'")
    grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
        grep -q 'Slave_SQL_Running: Yes' <<<"$output" &&
        grep -q 'Seconds_Behind_Master: 0' <<<"$output"
}

failover_to() {
    local target=$1
    valid_node "$target" || fail "Unknown node: $target"
    local source
    source=$(peer_of "$target")

    echo "Planned failover: $source -> $target"
    read -r -p "Type '$target' to continue: " confirmation
    [[ "$confirmation" == "$target" ]] || fail "Failover cancelled"

    echo "Stopping application on $source..."
    remote "$source" "systemctl stop '$SERVICE'"

    echo "Waiting for MariaDB replication on $target..."
    for _ in {1..30}; do
        replica_caught_up "$target" && break
        sleep 1
    done
    replica_caught_up "$target" || fail "MariaDB replica did not catch up"

    echo "Making MariaDB on $source read-only..."
    remote "$source" "mariadb -e 'SET GLOBAL read_only=ON'"

    echo "Promoting MariaDB on $target..."
    remote "$target" "mariadb -e 'STOP SLAVE; RESET SLAVE ALL; SET GLOBAL read_only=OFF'"

    echo "Starting application on $target..."
    remote "$target" "systemctl start '$SERVICE'"
    remote "$target" "systemctl is-active --quiet '$SERVICE'" ||
        fail "$SERVICE failed to start on $target"

    echo "Failover to $target completed."
}

promote() {
    local node
    node=$(hostname -s)
    valid_node "$node" || fail "This host is not bama or wintermute: $node"

    echo "Emergency promotion of $node may lose unreplicated transactions."
    read -r -p "Type 'promote $node' to continue: " confirmation
    [[ "$confirmation" == "promote $node" ]] || fail "Promotion cancelled"

    mariadb -e 'STOP SLAVE; RESET SLAVE ALL; SET GLOBAL read_only=OFF'
    systemctl start "$SERVICE"
    systemctl is-active --quiet "$SERVICE" || fail "$SERVICE failed to start"
    echo "$node promoted successfully."
}

demote() {
    local node peer user_sql password_sql primary_position output
    node=$(hostname -s)
    valid_node "$node" || fail "This host is not bama or wintermute: $node"
    [[ $EUID -eq 0 ]] || fail "This command must be run as root"
    peer=$(peer_of "$node")
    load_replication_credentials
    user_sql=$(sql_string "$XMR_REPLICATION_USER")
    password_sql=$(sql_string "$XMR_REPLICATION_PASSWORD")

    echo "Demoting $node will stop $SERVICE and replicate MariaDB from $peer."
    read -r -p "Type 'demote $node' to continue: " confirmation
    [[ "$confirmation" == "demote $node" ]] || fail "Demotion cancelled"

    systemctl stop "$SERVICE"
    mariadb -e 'SET GLOBAL read_only=ON'
    [[ "$(mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.read_only')" == "1" ]] ||
        fail "MariaDB is not read-only"

    primary_position=$(remote "$peer" \
        "mariadb --batch --skip-column-names -e 'SELECT @@GLOBAL.gtid_current_pos'")
    [[ "$primary_position" =~ ^[0-9]+-[0-9]+-[0-9]+(,[0-9]+-[0-9]+-[0-9]+)*$ ]] ||
        fail "Unable to determine the GTID position on $peer"

    mariadb -e 'STOP SLAVE' 2>/dev/null || true
    mariadb -e 'RESET SLAVE ALL'
    mariadb -e "SET GLOBAL gtid_slave_pos='$primary_position'"
    mariadb -e "
        CHANGE MASTER TO
            MASTER_HOST='$peer',
            MASTER_USER=$user_sql,
            MASTER_PASSWORD=$password_sql,
            MASTER_USE_GTID=slave_pos,
            MASTER_SSL=1,
            MASTER_SSL_VERIFY_SERVER_CERT=1;
        START SLAVE;
    "

    for _ in {1..10}; do
        output=$(mariadb -e 'SHOW SLAVE STATUS\G')
        if grep -q 'Slave_IO_Running: Yes' <<<"$output" &&
           grep -q 'Slave_SQL_Running: Yes' <<<"$output"; then
            echo "$node demoted successfully and replicating from $peer."
            return
        fi
        sleep 1
    done
    sed -n \
        -e '/Slave_IO_Running:/p' \
        -e '/Slave_SQL_Running:/p' \
        -e '/Last_IO_Error:/p' \
        -e '/Last_SQL_Error:/p' <<<"$output" >&2
    fail "MariaDB replication did not start on $node"
}

restart() {
    [[ $EUID -eq 0 ]] || fail "This command must be run as root"
    echo "Restarting $SERVICE on $(hostname -s)..."
    systemctl restart "$SERVICE"
    systemctl is-active --quiet "$SERVICE" || fail "$SERVICE failed to restart"
    echo "$SERVICE restarted successfully."
}

[[ $# -ge 1 ]] || { usage; exit 1; }

case "$1" in
    status)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        status
        ;;
    restart)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        restart
        ;;
    failover-to)
        [[ $# -eq 2 ]] || { usage; exit 1; }
        failover_to "$2"
        ;;
    promote)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        promote
        ;;
    demote)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        demote
        ;;
    *)
        usage
        exit 1
        ;;
esac
