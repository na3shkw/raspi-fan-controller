#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import json
import time

import fire
import pigpio


CONFIG_FILE = "./config.json"
DEBUG_CONFIG_FILE = "./debug_config.json"

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

def is_daemon_active():
    match = re.search("Active: ([^\s]+)\s", exec_cmd("make daemon.status"))
    return match.group(1) == "active"

def set_pwm(pin, frequency, duty):
    pi = pigpio.pi()
    pi.hardware_PWM(
        pin,
        frequency,
        int(1000000 * clamp(duty, 0, 1))
    )

def debug():
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
            set_pwm(config["gpio"]["pin"], frequency, duty)
            print(f"duty={duty}, freq={frequency}")
            duty_last = duty
            frequency_last = frequency

        time.sleep(2)


def main(debug=False):
    """
    ファン制御を実行する

    Args:
        debug (bool): デバッグモードを有効にするか
    """
    if debug:
        debug()
        return
    if is_daemon_active():
        print("Daemon is already active.")
        return

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
            config["gpio"]["pin"],
            frequency,
            duty
        )

        print(f"temp={temp}'C, duty={duty}, freq={frequency}")
        time.sleep(config["interval"])

if __name__ == "__main__":
    fire.Fire(main)
