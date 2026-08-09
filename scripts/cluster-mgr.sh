#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SERVICE="xmr.service"
readonly CLUSTER_SCRIPT="/opt/xmr_ops/cluster-mgr.sh"
readonly DB_SCRIPT="/opt/xmr_ops/db-mgr.sh"
readonly NODES=(bama wintermute)
readonly SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)
readonly LOCAL_NODE="$(hostname -s)"

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
    remote "$1" "cd '$BASE_DIR' && ./venv/bin/python -c 'from constants.DDefault import DDefault; print(DDefault.XMR_VERSION)'"
}

service_on() {
    remote "$1" "systemctl is-active '$SERVICE' 2>/dev/null || true"
}

db_role_on() {
    remote "$1" "'$DB_SCRIPT' role"
}

replication_on() {
    remote "$1" "'$DB_SCRIPT' replication"
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
    remote "$1" "'$DB_SCRIPT' replica-caught-up"
}

replica_healthy() {
    remote "$1" "'$DB_SCRIPT' replica-healthy"
}

failover_to() {
    local target=$1
    valid_node "$target" || fail "Unknown node: $target"
    local source
    source=$(peer_of "$target")

    echo "Planned failover: $source -> $target"
    read -r -p "Type '$target' to continue: " confirmation
    [[ "$confirmation" == "$target" ]] || fail "Failover cancelled"

    echo "Checking MariaDB replication on $target..."
    replica_healthy "$target" ||
        fail "$target is not a healthy MariaDB replica; no services were changed"

    echo "Stopping application on $source..."
    remote "$source" "systemctl stop '$SERVICE'"

    echo "Waiting for MariaDB replication on $target..."
    for _ in {1..30}; do
        replica_caught_up "$target" && break
        sleep 1
    done
    replica_caught_up "$target" || fail "MariaDB replica did not catch up"

    echo "Making MariaDB on $source read-only..."
    remote "$source" "'$DB_SCRIPT' set-read-only"

    echo "Promoting MariaDB on $target..."
    remote "$target" "'$DB_SCRIPT' promote"

    echo "Configuring $source as the new replica..."
    remote "$source" \
        "printf 'demote $source\\n' | '$CLUSTER_SCRIPT' demote"

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

    "$DB_SCRIPT" promote
    systemctl start "$SERVICE"
    systemctl is-active --quiet "$SERVICE" || fail "$SERVICE failed to start"
    echo "$node promoted successfully."
}

demote() {
    local node peer
    node=$(hostname -s)
    valid_node "$node" || fail "This host is not bama or wintermute: $node"
    [[ $EUID -eq 0 ]] || fail "This command must be run as root"
    peer=$(peer_of "$node")

    echo "Demoting $node will stop $SERVICE and replicate MariaDB from $peer."
    read -r -p "Type 'demote $node' to continue: " confirmation
    [[ "$confirmation" == "demote $node" ]] || fail "Demotion cancelled"

    systemctl stop "$SERVICE"
    "$DB_SCRIPT" demote-to "$peer"
    echo "$node demoted successfully and replicating from $peer."
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
