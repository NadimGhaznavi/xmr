#!/bin/bash
# Run the checks required before creating a release.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly PYTHON_PATHS=(admin constants db mgr tests web)
readonly PYTHON_FILES=(admin/*.py constants/*.py db/*.py mgr/*.py tests/*.py web/*.py)

cd "$PROJECT_DIR"

require_command() {
    local command_name=$1

    if ! command -v "$command_name" >/dev/null 2>&1; then
        printf 'ERROR: Required command not found: %s\n' "$command_name" >&2
        exit 1
    fi
}

run_check() {
    local description=$1
    shift

    printf '\n==> %s\n' "$description"
    "$@"
}

check_formatting() {
    local source_file

    for source_file in "${PYTHON_FILES[@]}"; do
        black --check --quiet "$source_file"
    done

    printf '%d Python files comply with Black.\n' "${#PYTHON_FILES[@]}"
}

main() {
    require_command pytest
    run_check "Running tests" pytest -v

    require_command black
    run_check "Checking formatting" check_formatting

    require_command isort
    run_check "Checking import order" isort --check-only "${PYTHON_PATHS[@]}"

    require_command flake8
    run_check "Linting" flake8 "${PYTHON_PATHS[@]}"

    require_command mypy
    run_check "Checking types" mypy "${PYTHON_PATHS[@]}"

    require_command bandit
    run_check "Checking for security issues" bandit -r admin constants db mgr web

    printf '\nAll pre-release checks passed.\n'
}

main "$@"
