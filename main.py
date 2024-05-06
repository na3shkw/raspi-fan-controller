#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import json
import time
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


def main():
    # 設定を読み込み
    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = json.load(f)

    # CPU温度を取得
    temp = get_cpu_temperature()

    # Duty比を計算
    duty = None
    duty_rates = config["pwm"]["duty_rates"]
    for i, threshold in enumerate(config["pwm"]["thresholds"]):
        if temp < threshold:
            duty = duty_rates[i]
            break
    if duty is None:
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

if __name__ == "__main__":
    if is_daemon_active():
        main()
    else:
        debug()
