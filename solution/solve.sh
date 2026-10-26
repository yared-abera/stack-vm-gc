#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${APP_DIR}/vm"
cp "${SCRIPT_DIR}/machine.py" "${APP_DIR}/vm/machine.py"
cp "${SCRIPT_DIR}/run.py" "${APP_DIR}/vm/run.py"
