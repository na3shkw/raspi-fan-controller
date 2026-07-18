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

def clamp(num, minimum, maximum):
    return max(minimum, min(maximum, num))

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
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print(f"PID file {PID_FILE} created with PID {os.getpid()}", flush=True)

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

def check_pwm_params(config):
    """
    PWM制御の設定値が正しいかチェックする

    Args:
        config (dict): 設定値
    """
    curve = config["pwm"]["curve"]
    frequency = config["pwm"]["frequency"]

    # カーブは1点以上
    if len(curve) < 1:
        raise ValueError("pwm.curve must have at least one point.")
    # 各点はtemperature/dutyを持つ
    if any("temperature" not in point or "duty" not in point for point in curve):
        raise ValueError("Each point in pwm.curve must have 'temperature' and 'duty' keys.")
    # temperatureは整数
    if any(not isinstance(point["temperature"], int) for point in curve):
        raise TypeError("temperature must be an integer.")
    # dutyは0以上1以下
    if any(point["duty"] < 0 or point["duty"] > 1 for point in curve):
        raise ValueError("duty must be between 0 and 1.")
    # temperatureは昇順に並んでいる（重複不可）
    temperatures = [point["temperature"] for point in curve]
    if temperatures != sorted(set(temperatures)):
        raise ValueError("temperature must be in strictly ascending order.")
    # frequencyはdefault/low_clockを持つオブジェクト
    if not isinstance(frequency, dict) or "default" not in frequency or "low_clock" not in frequency:
        raise ValueError("pwm.frequency must be an object with 'default' and 'low_clock' keys.")

def build_temp_duty_map(curve):
    """
    温度に対するDuty比のマッピングを線形補完して事前に計算する

    Args:
        curve (list): {temperature, duty}のリスト（temperature昇順）

    Returns:
        tuple: (temperatures, duties, temp_duty_map)
    """
    temperatures = [point["temperature"] for point in curve]
    duties = [point["duty"] for point in curve]

    temp_duty_map = {}
    for i in range(len(temperatures) - 1):
        for temp in range(temperatures[i], temperatures[i + 1]):
            temp_duty_map[temp] = duties[i] + \
                (duties[i + 1] - duties[i]) * (temp - temperatures[i]) \
                / (temperatures[i + 1] - temperatures[i])

    return temperatures, duties, temp_duty_map

def resolve_duty(temp, temperatures, duties, temp_duty_map):
    """
    CPU温度からDuty比を決定する

    Args:
        temp (float): CPU温度
        temperatures (list): build_temp_duty_mapが返したtemperatures
        duties (list): build_temp_duty_mapが返したduties
        temp_duty_map (dict): build_temp_duty_mapが返したtemp_duty_map

    Returns:
        float: Duty比
    """
    temp_rounded = round(temp)

    if temp_rounded in temp_duty_map:
        return temp_duty_map[temp_rounded]
    elif temp <= temperatures[0]:
        return duties[0]
    else:
        return duties[-1]

def main(debug=False):
    """
    ファン制御を実行する

    Args:
        debug (bool): デバッグモードを有効にするか
    """

    # 重複実行制御
    if is_daemon_active():
        print("Fan controller is already running.", flush=True)
        exit(1)

    pi = pigpio.pi()

    try:
        write_pid()

        # デバッグモード
        if debug:
            debug_run(pi)
            return

        # 設定を読み込み
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)

        # PWM制御の設定値が正しいかチェック
        check_pwm_params(config)

        # 温度に対するDuty比のマッピングを線形補完して事前に計算
        temperatures, duties, temp_duty_map = build_temp_duty_map(config["pwm"]["curve"])

        while True:
            # CPU温度を取得
            temp = get_cpu_temperature()

            # Duty比を決定
            duty = resolve_duty(temp, temperatures, duties, temp_duty_map)

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
