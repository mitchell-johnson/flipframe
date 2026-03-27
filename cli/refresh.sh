#!/bin/bash
# FlipFrame daily refresh — run via cron (e.g. 5:30 AM)
# Adjust the PATH and cd path for your environment
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."
python3 cli/flipframe.py push >> /tmp/flipframe-cron.log 2>&1
echo "--- $(date) ---" >> /tmp/flipframe-cron.log
