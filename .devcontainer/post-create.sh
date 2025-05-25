#!/bin/bash

# Install uv
pip install uv==0.7.8

# Install the requirements
cd /workspaces/raspi-fan-controller
make uv.init

# Install the mock vcgencmd
EXECUTABLE=/workspaces/raspi-fan-controller/mock/vcgencmd/vcgencmd_mock.py
DEST_DIR=$HOME/.local/bin
DEST_PATH="$DEST_DIR/vcgencmd"

mkdir -p "$DEST_DIR"
ln -s "$EXECUTABLE" "$DEST_PATH"
chmod +x "$DEST_PATH"
