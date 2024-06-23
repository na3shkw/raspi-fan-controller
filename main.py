#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import json
import time

import fire
import pigpio


CONFIG_FILE = "./config.json"
DEBUG_CONFIG_FILE = "./debug_config.json"
PID_FILE = "fancontrol.pid"

def clamp(num, minimun, maximum):
    return max(minimun, min(maximum, num))

def exec_cmd(command):
    result = subprocess.run(
        command.split(" "),
        stdout=subprocess.PIPE,
        stderr = subprocess.DEVNULL
    )
    return result.stdout.decode("utf-8")

def get_cpu_temperature():
    match = re.search("temp=([\d|\.]+)", exec_cmd("vcgencmd measure_temp"))
    return float(match.group(1))

def get_pwm_clock():
    match = re.search("=(\d+)", exec_cmd("vcgencmd measure_clock pwm"))
    return int(match[1])

def write_pid():
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        print(f"PID file {PID_FILE} created with PID {os.getpid()}", flush=True)
    except Exception as e:
        print(f"Failed to write PID file {PID_FILE}: {e}", flush=True)

def is_daemon_active():
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        if os.path.exists(f"/proc/{pid}"):
            return True
        else:
            os.remove(PID_FILE)
    return False

def set_pwm(pi, pin, frequency, duty):
    pi.hardware_PWM(
        pin,
        frequency,
        int(1000000 * clamp(duty, 0, 1))
    )

def debug_run(pi):
    try:
        duty_last = None
        frequency_last = None
        while True:
            # 設定を読み込み
            with open(DEBUG_CONFIG_FILE, encoding="utf-8") as f:
                config = json.load(f)
            duty = config["pwm"]["duty"]
            frequency = config["pwm"]["frequency"]

            # 前回の設定値と比較
            if duty != duty_last or frequency != frequency_last:
                set_pwm(pi, config["gpio"]["pin"], frequency, duty)
                print(f"duty={duty}, freq={frequency}")
                duty_last = duty
                frequency_last = frequency

            time.sleep(config["interval"])
    finally:
        pi.stop()


def main(debug=False):
    """
    ファン制御を実行する

    Args:
        debug (bool): デバッグモードを有効にするか
    """

    # 重複実行制御
    if is_daemon_active():
        print("Daemon is already active.", flush=True)
        exit(1)

    pi = pigpio.pi()

    # デバッグモード
    if debug:
        debug_run(pi)
        return

    try:
        write_pid()

        # 設定を読み込み
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)

        # 温度に対するDuty比のマッピングを線形補完して事前に計算
        temp_duty_map = {}
        thresholds = config["pwm"]["thresholds"]
        duty_rates = config["pwm"]["duty_rates"]
        for i in range(len(thresholds) - 1):
            for temp in range(thresholds[i], thresholds[i + 1]):
                temp_duty_map[temp] = duty_rates[i] + \
                    (duty_rates[i + 1] - duty_rates[i]) * (temp - thresholds[i]) \
                    / (thresholds[i + 1] - thresholds[i])

        while True:
            # CPU温度を取得
            temp = get_cpu_temperature()
            temp_rounded = round(temp)

            # Duty比を決定
            if temp_rounded in temp_duty_map:
                duty = temp_duty_map[temp_rounded]
            elif temp <= thresholds[0]:
                duty = duty_rates[0]
            else:
                duty = duty_rates[-1]

            # 周波数を決定
            # Xサーバーでログインするとデューティー比0.5付近から不安定になるので周波数を試験的に調整
            frequency = config["pwm"]["frequency"]["default"]
            if get_pwm_clock() < 200000000:
                frequency = config["pwm"]["frequency"]["low_clock"]

            # GPIO設定
            set_pwm(
                pi,
                config["gpio"]["pin"],
                frequency,
                duty
            )

            print(f"temp={temp}'C, duty={round(duty, 2)}, freq={frequency}", flush=True)
            time.sleep(config["interval"])
    finally:
        pi.stop()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"PID file {PID_FILE} removed", flush=True)

if __name__ == "__main__":
    fire.Fire(main)
