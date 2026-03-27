#!/bin/bash
# FlipFrame daily refresh — run via cron at 5:30 AM
export PATH="/Users/mitchell/Library/Python/3.14/bin:/opt/homebrew/bin:$PATH"
export PYTHONUNBUFFERED=1
cd /Users/mitchell/.openclaw/workspace/flipoff
python3 cli/flipframe.py push >> /tmp/flipframe-cron.log 2>&1
echo "--- $(date) ---" >> /tmp/flipframe-cron.log
