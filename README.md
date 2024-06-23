# Raspberry Pi Fan Controller

## 概要
Raspberry PiのファンをPWM制御するためのコントローラ―です。
システムの起動後にデーモンとして常駐し、30秒に一度の間隔でCPU温度に応じてファンの回転速度を制御します。

## システム要件
[pigpio](https://abyz.me.uk/rpi/pigpio/index.html)が必要です。

```bash
$ sudo apt install pigpio
$ pip3 install pigpio
```

次のコマンドを実行し、pigpioデーモンがシステムの起動後に開始するようにしておきます。

```bash
$ sudo systemctl enable pigpiod
```

## 初期設定
1. `$ sudo make init`を実行して設定ファイルとサービス用のファイルを作成します。
    - `config.json`と`fancontrol.service`が作成されます。
2. `config.json`でPWM制御に利用するGPIOピン番号を`gpio.pin`に設定します。
    - 参考: [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
3. `$ sudo systemctl start pigpiod`を実行してpigpioデーモンを起動します。
    - SSH経由で実行して起動に失敗する場合は、`$ sudo raspi-config`の画面から`Remote GPIO`を`enable`にする必要があります。
4. `$ sudo make daemon.enable`を実行してシステムにサービスを登録します。
5. `config.json`を編集してGPIOピンやPWMの周波数・CPUの温度に対するデューティー比の設定を行います。
    - ファンが回転しない・低デューティー比で不安定になる場合は`config.json`の`pwm.frequency`を調整する必要があります。

## デバッグ
CPU温度に応じたファンの自動制御を行わず、指定したパラメータでファンを回転させます。

1. `$ cp ./debug_config.example.json ./debug_config.json`を実行してデバッグ用の設定ファイルを作成します。
    - `debug_config.json`が作成されます。
2. `debug_config.json`でPWM制御に利用するGPIOピン番号などを設定します。
3. デーモンが既に起動している場合は`$ sudo make daemon.stop`を実行してデーモンを停止します。
4. `python main.py --debug`を実行してデバッグモードでファンを制御します。
    - デバッグモードでは`debug_config.json`を定期的に読み込みます。
    - 標準出力にCPU温度とデューティー比が表示されます。

## 参考文献
- [pigpio Python interface](https://abyz.me.uk/rpi/pigpio/python.html)
- [systemd.service - freedesktop.org](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [4. Configuring Remote GPIO &mdash; GPIO Zero 1.6.2 Documentation](https://gpiozero.readthedocs.io/en/stable/remote_gpio.html)
- [#517 Hardware PMW function not working on Pi4B revision 1.4](https://github.com/joan2937/pigpio/issues/517)
