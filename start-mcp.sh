#!/bin/bash
set -euo pipefail
source ~/.config/markbase/markbase.env 2>/dev/null || true
exec python "$(dirname "$0")/mcp_server.py"
