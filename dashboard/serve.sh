#!/usr/bin/env bash
# Regenerate dashboard then serve on localhost:8042
set -e
DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"
SECOND_BRAIN="$(dirname "$DASHBOARD_DIR")"

echo "🔄 Regenerating dashboard..."
python3 "$DASHBOARD_DIR/generate.py"

echo "🚀 Serving on http://localhost:8042"
cd "$DASHBOARD_DIR"
exec python3 -m http.server 8042
