#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SERVICE="xmr.service"
readonly NODES=(bama wintermute)
readonly SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)

usage() {
    echo "Usage:" >&2
    echo "  $0 status" >&2
    echo "  $0 failover-to <bama|wintermute>" >&2
    echo "  $0 promote" >&2
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

remote() {
    local node=$1
    shift
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

[[ $# -ge 1 ]] || { usage; exit 1; }

case "$1" in
    status)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        status
        ;;
    failover-to)
        [[ $# -eq 2 ]] || { usage; exit 1; }
        failover_to "$2"
        ;;
    promote)
        [[ $# -eq 1 ]] || { usage; exit 1; }
        promote
        ;;
    *)
        usage
        exit 1
        ;;
esac
