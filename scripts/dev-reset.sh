#!/bin/bash

#!/bin/bash
set -euo pipefail

BASE_DIR="/opt/xmr"

echo "Removing installation directory ($BASE_DIR)..."
rm -rf -- "$BASE_DIR"

echo "Bear and Moose XMR installation removed successfully!"

