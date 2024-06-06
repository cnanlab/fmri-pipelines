#!/bin/bash

BASE_DIR="."

count=0

for dir in "$BASE_DIR"/sub-*/; do
  if [ -d "$dir/stats" ]; then
    count=$((count + 1))
  fi
done

echo "Number of directories containing a 'stats' directory: $count"

TOTAL_DIRS=$(ls | wc -l)

echo "Total directors: $TOTAL_DIRS"
