#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import json
import pigpio


CONFIG_FILE = "./config.json"

def clamp(num, minimun, maximum):
    return max(minimun, min(maximum, num))

def get_cpu_temperature():
    result = subprocess.run(["vcgencmd", "measure_temp"], stdout=subprocess.PIPE)
    match = re.search("temp=([\d|\.]+)", result.stdout.decode("utf-8"))
    return float(match.group(1))

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

    # GPIO設定
    pi = pigpio.pi()
    pi.hardware_PWM(
        config["gpio"]["pin"],
        config["pwm"]["frequency"],
        int(1000000 * clamp(duty, 0, 1))
    )

    print(f"temp={temp}'C, duty={duty}")

if __name__ == "__main__":
    main()
