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

## TODO
- [ ] CPU温度の閾値とデューティー比の設定の整合性をチェックする
- [ ] デューティー比を固定してファンを回転させるモードを追加

## 参考文献
- [pigpio Python interface](https://abyz.me.uk/rpi/pigpio/python.html)
- [systemd.service - freedesktop.org](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [4. Configuring Remote GPIO &mdash; GPIO Zero 1.6.2 Documentation](https://gpiozero.readthedocs.io/en/stable/remote_gpio.html)
