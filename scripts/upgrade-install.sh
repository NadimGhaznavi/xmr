#!/bin/bash
set -euo pipefail

readonly BASE_DIR="/opt/xmr"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly REMOTE="origin"

usage() {
    echo "Usage: $0 <git-tag>" >&2
    echo "Example: $0 v0.0.6" >&2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ $# -ne 1 ]]; then
    usage
    exit 1
fi

readonly TAG="$1"
[[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "Invalid release tag: $TAG"
[[ $EUID -eq 0 ]] || fail "This script must be run as root"
[[ -d "$BASE_DIR" ]] || fail "$BASE_DIR is not installed"
[[ -x "$BASE_DIR/venv/bin/pip" ]] || fail "The XMR Python environment is missing"

for command in git tar install mktemp; do
    command -v "$command" >/dev/null 2>&1 || fail "Required command not found: $command"
done

cd "$REPO_DIR"

readonly TEMP_DIR="$(mktemp -d)"
readonly RELEASE_REF="refs/xmr-upgrades/$TAG"
trap 'rm -rf -- "$TEMP_DIR"' EXIT

echo "Fetching $TAG from $REMOTE..."
git fetch --no-tags "$REMOTE" "+refs/tags/$TAG:$RELEASE_REF"
git rev-parse --verify --quiet "$RELEASE_REF^{commit}" >/dev/null ||
    fail "Tag not found: $TAG"

readonly MANIFEST_PATH="releases/$TAG.manifest"
git show "$RELEASE_REF:$MANIFEST_PATH" >"$TEMP_DIR/manifest" ||
    fail "Release does not contain $MANIFEST_PATH"

declare -a FILES=()
declare -A SEEN=()
changed_count=0

while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    [[ "$line" =~ ^([*.])[[:space:]]([^[:space:]].*)$ ]] ||
        fail "Invalid manifest entry: $line"

    marker="${BASH_REMATCH[1]}"
    path="${BASH_REMATCH[2]}"
    [[ "$path" != /* && "$path" != ".." && "$path" != ../* && "$path" != */../* && "$path" != */.. ]] ||
        fail "Unsafe manifest path: $path"
    [[ -z "${SEEN[$path]+present}" ]] || fail "Duplicate manifest path: $path"
    git cat-file -e "$RELEASE_REF:$path" 2>/dev/null ||
        fail "Manifest file is absent from $TAG: $path"

    SEEN["$path"]=1
    FILES+=("$path")
    [[ "$marker" == "*" ]] && changed_count=$((changed_count + 1))
done <"$TEMP_DIR/manifest"

[[ ${#FILES[@]} -gt 0 ]] || fail "Manifest contains no files"

mkdir "$TEMP_DIR/release"
git archive --format=tar "$RELEASE_REF" -- "${FILES[@]}" |
    tar -xf - -C "$TEMP_DIR/release"

echo "Release: $TAG"
echo "Managed files: ${#FILES[@]}"
echo "Changed files: $changed_count"
echo "Installing into $BASE_DIR..."

for path in "${FILES[@]}"; do
    mode=0644
    [[ "$path" == scripts/*.sh ]] && mode=0755
    install -D -o root -g root -m "$mode" \
        "$TEMP_DIR/release/$path" "$BASE_DIR/$path"
done

if [[ -f "$TEMP_DIR/release/requirements.txt" ]]; then
    "$BASE_DIR/venv/bin/pip" install --requirement "$BASE_DIR/requirements.txt"
fi

install -o root -g root -m 0644 /dev/null "$BASE_DIR/etc/installed-release"
printf '%s\n' "$TAG" >"$BASE_DIR/etc/installed-release"

echo "Installed $TAG successfully."
echo "Use cluster-mgr.sh failover-to <node> when ready."
