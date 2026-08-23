#!/bin/bash
set -uo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly DEFAULT_INDEX="$SCRIPT_DIR/../index.md"

usage() {
    echo "Usage: $0 [index.md]" >&2
}

if [[ $# -gt 1 ]]; then
    usage
    exit 2
fi

readonly INDEX_FILE="${1:-$DEFAULT_INDEX}"

if [[ ! -r "$INDEX_FILE" ]]; then
    echo "Cannot read $INDEX_FILE" >&2
    exit 2
fi

if ! command -v dig >/dev/null 2>&1; then
    echo "This report requires the 'dig' command." >&2
    exit 2
fi

declare -a environments=()
declare -a components=()
declare -a dns_names=()

while IFS=$'\t' read -r environment component dns_name; do
    environments+=("$environment")
    components+=("$component")
    dns_names+=("$dns_name")
done < <(
    awk '
        function trim(value) {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            return value
        }

        /^## Development Environment[[:space:]]*$/ { environment = "DEV" }
        /^## QA Environment[[:space:]]*$/          { environment = "QA" }
        /^## Production Environment[[:space:]]*$/  { environment = "PROD" }

        /^\|/ {
            component = trim($2)
            record_type = trim($3)
            dns_name = trim($4)
            gsub(/`/, "", dns_name)
            sub(/[[:space:]]+([Ss]ervice|VIP)$/, "", component)

            if (environment != "" && record_type == "CNAME") {
                printf "%s\t%s\t%s\n", environment, component, dns_name
            }
        }
    ' FS='|' "$INDEX_FILE"
)

missing=0
declare -a targets=()
environment_width=11
component_width=7
dns_name_width=8
target_width=11

for i in "${!dns_names[@]}"; do
    target=$(dig +short CNAME "${dns_names[$i]}" | sed -n '1p')
    if [[ -z "$target" ]]; then
        target='NOT FOUND'
        missing=1
    else
        target=${target%.}
    fi

    targets+=("$target")
    ((${#environments[$i]} > environment_width)) && environment_width=${#environments[$i]}
    ((${#components[$i]} > component_width)) && component_width=${#components[$i]}
    ((${#dns_names[$i]} > dns_name_width)) && dns_name_width=${#dns_names[$i]}
    ((${#target} > target_width)) && target_width=${#target}
done

printf "%-${environment_width}s  %-${component_width}s  %-${dns_name_width}s  %-${target_width}s\n" \
    'Environment' 'Service' 'DNS name' 'Resolves to'
printf '%*s  %*s  %*s  %*s\n' \
    "$environment_width" '' \
    "$component_width" '' \
    "$dns_name_width" '' \
    "$target_width" '' | tr ' ' '-'

for i in "${!dns_names[@]}"; do
    printf "%-${environment_width}s  %-${component_width}s  %-${dns_name_width}s  %-${target_width}s\n" \
        "${environments[$i]}" \
        "${components[$i]}" \
        "${dns_names[$i]}" \
        "${targets[$i]}"
done

exit "$missing"
