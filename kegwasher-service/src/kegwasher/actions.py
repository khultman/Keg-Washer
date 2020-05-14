# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import threading

class Actions(threading.Thread):
    def __init__(self, *args, **kwargs):
        pass


    def abort(self):
        log.debug(f'Aborted\nPress Enter')
        self._display.clear()
        self._display.message(f'Aborted\nPress Enter')

    def execute_mode(self):
        log.debug(f'Executing Mode: {self._modes.data["display_name"]}')
        operations = self._modes.data.get('operations')
        for cmd, t in operations:
            log.debug(f'Cmd: {cmd}, time: {t}')
            self._mode_map[cmd]()
            for i in range(0, t):
                self._display.clear()
                self._display.message(f'{cmd}\nTime Left: {t - i}')
                time.sleep(1)

    def select_mode(self):
        log.debug(f'Select Mode: {self._modes.data["display_name"]}')
        self._display.clear()
        self._display.message(f'Select Mode\n{self._modes.data["display_name"]}')