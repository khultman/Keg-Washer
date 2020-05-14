# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

from kegwasher.config import pin_config, mode_config
from kegwasher.service import KegWasher

if __name__ == '__main__':
    keg_washer = KegWasher(pin_config, mode_config)
    keg_washer.daemon = True
    keg_washer.start()