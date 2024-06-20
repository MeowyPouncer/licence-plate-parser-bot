#!/bin/bash
LOGFILE="volume/logs/run_every_second.log"

while true; do
    if ! pgrep -f /app/main.py; then
        echo "$(date "+%Y-%m-%d %H:%M:%S") - Starting main.py" >> "$LOGFILE"
        python /app/main.py >> "$LOGFILE" 2>&1
    fi
    sleep 1
done