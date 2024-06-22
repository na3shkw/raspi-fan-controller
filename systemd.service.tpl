[Unit]
Description=Fan Controller

[Service]
Type=simple
ExecStart=${FAN_CONTROLLER_DIR}/main.py
WorkingDirectory=${FAN_CONTROLLER_DIR}

[Install]
WantedBy=multi-user.target
