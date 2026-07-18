#!/bin/bash
cd "$WORKSPACE_FOLDER"

# Install uv
curl -LsSf https://astral.sh/uv/0.11.29/install.sh | sh

# Install dependency
uv sync --frozen

# Install stub vcgencmd
VCGENCMD="$HOME/.local/bin/vcgencmd"
cat > "$VCGENCMD" <<EOF
#!/bin/sh
exec "$UV_PROJECT_ENVIRONMENT/bin/python" "$WORKSPACE_FOLDER/stub/vcgencmd/vcgencmd_stub.py" "\$@"
EOF
chmod +x "$VCGENCMD"
