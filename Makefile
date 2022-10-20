daemonName := fancontrol
daemonPath := /etc/systemd/system/$(daemonName).service

init:
	@cp ./config.example.json ./config.json
	@make service.generate

service.generate: export FAN_CONTROLLER_DIR := $(shell pwd)
service.generate:
ifeq ("$(wildcard ./$(daemonName).service)", "")
	@cat systemd.service.tpl | envsubst > ./$(daemonName).service
endif

daemon.reload:
	@sudo systemctl daemon-reload

daemon.enable:
	@sudo ln -s `pwd`/$(daemonName).service $(daemonPath)
	@make daemon.reload
	@sudo systemctl enable $(daemonName)
	@echo "Daemon $(daemonName) enabled"

daemon.disable:
	@sudo unlink $(daemonPath)
	@make daemon.reload
	@echo "Daemon $(daemonName) disabled"

daemon.start:
	@sudo systemctl start $(daemonName)

daemon.stop:
	@sudo systemctl stop $(daemonName)

daemon.status:
	@systemctl status $(daemonName)

daemon.log:
	journalctl -u $(daemonName)

daemon.livelog:
	journalctl -f -u $(daemonName)
