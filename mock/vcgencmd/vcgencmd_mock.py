#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import fire

RETURN_VALUE_CONFIG = '/workspaces/raspi-fan-controller/mock/vcgencmd/return_values.json'

class Vcgencmd(object):
    """
    vcgencmdのモッククラス
    """
    def __init__(self):
        with open(RETURN_VALUE_CONFIG) as f:
            self.return_values = json.load(f)

    def measure_temp(self):
        temp = self.return_values['measure_temp']
        return f'temp={temp:.1f}\'C'

    def measure_clock(self, *args):
        clock = self.return_values['measure_clock']
        return f'frequency(25)={clock:.0f}'

if __name__ == "__main__":
    fire.Fire(Vcgencmd)
