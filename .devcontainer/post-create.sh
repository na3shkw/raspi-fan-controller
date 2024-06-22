#!/bin/bash

# Make link to Python
sudo ln -s /usr/local/python/current/bin/python /usr/bin/python

# Install the mock vcgencmd
EXECUTABLE=/workspaces/raspi-fan-controller/mock/vcgencmd/vcgencmd_mock.py
DEST_DIR=/home/vscode/.local/bin
DEST_PATH="$DEST_DIR/vcgencmd"

mkdir -p "$DEST_DIR"
ln -s "$EXECUTABLE" "$DEST_PATH"
chmod +x "$DEST_PATH"
