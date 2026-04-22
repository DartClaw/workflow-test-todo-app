#!/bin/bash
set -e

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Install dependencies
echo "Syncing dependencies..."
uv sync

# Run the server
echo "Starting server..."
# We use exec so the shell process is replaced by uvicorn, handling signals correctly
exec uv run uvicorn app.main:app --reload --host 0.0.0.0
