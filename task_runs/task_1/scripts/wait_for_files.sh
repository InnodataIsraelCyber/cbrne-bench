#!/bin/bash

# Wait for files from previous stage
TARGET_DIR=$1
TARGET_FILE=$2
MAX_WAIT=${3:-300}  # 5 minutes default

if [ -z "$TARGET_DIR" ] || [ -z "$TARGET_FILE" ]; then
    echo "Usage: wait_for_files.sh <directory> <filename_pattern> [max_wait_seconds]"
    exit 1
fi

START_TIME=$(date +%s)

while true; do
    if [ -f "$TARGET_DIR/$TARGET_FILE" ]; then
        echo "Found $TARGET_DIR/$TARGET_FILE"
        break
    fi

    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -gt $MAX_WAIT ]; then
        echo "Timeout waiting for $TARGET_DIR/$TARGET_FILE after $MAX_WAIT seconds"
        break
    fi

    sleep 2
done

# List what we found
if [ -d "$TARGET_DIR" ]; then
    echo "Files in $TARGET_DIR:"
    ls -la "$TARGET_DIR" | tail -20
else
    echo "Directory $TARGET_DIR does not exist"
fi
