[Unit]
Description=Fan Controller

[Service]
Type=simple
ExecStart=${FAN_CONTROLLER_DIR}/main.py
WorkingDirectory=${FAN_CONTROLLER_DIR}
User=${USER}
StandardOutput=journal
StandardError=journal
Restart=on-failure
PIDFile=${FAN_CONTROLLER_DIR}/fancontrol.pid
ExecStopPost=/bin/rm -f ${FAN_CONTROLLER_DIR}/fancontrol.pid

[Install]
WantedBy=multi-user.target
