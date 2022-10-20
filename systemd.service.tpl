[Unit]
Description=Fan Controller

[Service]
Type=simple
ExecStart=${FAN_CONTROLLER_DIR}/main.py
WorkingDirectory=${FAN_CONTROLLER_DIR}
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
