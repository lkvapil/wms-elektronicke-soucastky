#!/bin/bash
# Launcher pro BOM Scanner
# Používá Python z ordersManager projektu, který má PyQt6

PYTHON_PATH="/Users/lukaskvapil/Documents/api-test/production/versionsMain/version1.24/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/bom_scanner.py"

echo "🚀 Spouštím BOM Scanner..."
echo "📂 Skript: $SCRIPT_PATH"
echo "🐍 Python: $PYTHON_PATH"
echo ""

"$PYTHON_PATH" "$SCRIPT_PATH"
