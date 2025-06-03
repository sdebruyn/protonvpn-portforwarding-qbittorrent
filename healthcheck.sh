#!/bin/sh

timestamp_file="/app/last_updated"

if [ ! -f "$timestamp_file" ]; then
  echo "Timestamp file missing"
  exit 1
fi

now=$(date +%s)
last=$(cat "$timestamp_file")
diff=$((now - last))

if [ "$diff" -lt 60 ]; then
  exit 0
else
  echo "Timestamp too old: $diff seconds"
  exit 1
fi
