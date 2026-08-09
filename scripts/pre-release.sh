#!/bin/bash
# Run the checks required before creating a release.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly DEV_ENV="$PROJECT_DIR/venv_dev"
readonly DEV_PYTHON="$DEV_ENV/bin/python"
readonly DEV_REQUIREMENTS="$PROJECT_DIR/requirements-dev.txt"
readonly PYTHON_PATHS=(admin constants db mgr tests web)
readonly PYTHON_FILES=(admin/*.py constants/*.py db/*.py mgr/*.py tests/*.py web/*.py)
readonly SHELL_FILES=(scripts/*.sh)

cd "$PROJECT_DIR"

fail() {
    printf 'ERROR: %s\n' "$1" >&2
    exit 1
}

run_check() {
    local description=$1
    shift

    printf '\n==> %s\n' "$description"
    "$@"
}

verify_dev_environment() {
    [[ -f "$DEV_REQUIREMENTS" ]] ||
        fail "Development requirements are missing: $DEV_REQUIREMENTS"

    if [[ ! -x "$DEV_PYTHON" ]]; then
        printf 'ERROR: Development environment is missing: %s\n' "$DEV_ENV" >&2
        printf 'Create it with:\n' >&2
        printf '  python3 -m venv %q\n' "$DEV_ENV" >&2
        printf '  %q -m pip install --requirement %q\n' \
            "$DEV_PYTHON" "$DEV_REQUIREMENTS" >&2
        exit 1
    fi

    "$DEV_PYTHON" -m pip check
    "$DEV_PYTHON" -m pip install \
        --dry-run \
        --no-index \
        --quiet \
        --requirement "$DEV_REQUIREMENTS"
}

check_formatting() {
    "$DEV_PYTHON" -m black --version
    "$DEV_PYTHON" -m black --check "${PYTHON_PATHS[@]}"
    printf 'Black checked %d Python files.\n' "${#PYTHON_FILES[@]}"
}

check_import_order() {
    printf 'isort %s\n' "$("$DEV_PYTHON" -m isort --version-number)"
    "$DEV_PYTHON" -m isort --check-only "${PYTHON_PATHS[@]}"
    printf 'isort checked %d Python files; 0 incorrectly sorted.\n' \
        "${#PYTHON_FILES[@]}"
}

check_linting() {
    "$DEV_PYTHON" -m flake8 --version
    "$DEV_PYTHON" -m flake8 --statistics "${PYTHON_PATHS[@]}"
    printf 'Flake8 checked %d Python files; 0 violations.\n' \
        "${#PYTHON_FILES[@]}"
}

main() {
    run_check "Validating development environment" verify_dev_environment
    run_check "Running tests" "$DEV_PYTHON" -m pytest -v
    run_check "Checking formatting" check_formatting
    run_check "Checking import order" check_import_order
    run_check "Linting" check_linting
    run_check "Checking types" "$DEV_PYTHON" -m mypy "${PYTHON_PATHS[@]}"
    run_check \
        "Checking for security issues" \
        "$DEV_PYTHON" -m bandit -r admin constants db mgr web
    run_check "Checking shell syntax" /bin/bash -n "${SHELL_FILES[@]}"

    printf '\nAll pre-release checks passed.\n'
}

main "$@"
