# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import ctypes
import logging
import os
import threading
import time

from kegwasher.exceptions import AbortException

log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))


class Action(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self._action = kwargs.get('action')
        self._hardware = kwargs.get('hardware', None)
        self._modes = kwargs.get('modes', None)
        self._operations = kwargs.get('operations', None)
        self._state = kwargs.get('state', None)
        self._threads = kwargs.get('threads', None)
        #
        self._mode_operation_map = {
            'air_fill_closed': self._operations.air_fill_closed,
            'air_fill_open':   self._operations.air_fill_open,
            'clean_closed':    self._operations.clean_closed,
            'clean_open':      self._operations.clean_open,
            'cleaner_fill':    self._operations.cleaner_fill,
            'co2_fill_closed': self._operations.co2_fill_closed,
            'co2_fill_open':   self._operations.co2_fill_open,
            'drain':           self._operations.drain,
            'rinse':           self._operations.rinse,
            'sanitize':        self._operations.sanitize,
            'sanitizer_fill':  self._operations.sanitizer_fill
        }

    def get_tid(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def abort_thread(self):
        tid = self.get_tid()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise AbortException('Halting Thread')

    def abort(self):
        if self._state['aborted'] and self._hardware.get('switches').get('abort').state:
            log.debug(f'Already Aborted, passing')
            pass
        elif not self._hardware.get('switches').get('abort').state:
            log.debug(f'Abort switch reset, resuming operation')
            self._state['aborted'] = False
            self._state['button_lock'] = False
            self._state['status'] = 'initialize'
        else:
            log.debug(f'Aborting')
            self._operations.all_off_closed()
            self._state['aborted'] = True
            self._state['status'] = 'aborted'
            for t in self._threads:
                if t is self:
                    log.debug('Abort thread itself is not committing suicide')
                else:
                    log.debug(f'Shooting thread {t.get_tid()} in the head')
                    t.abort_thread()
                    self._threads.remove(t)
            self._hardware.get('display').clear()
            self._hardware.get('display').message(f'Aborted\nReset Controller')

    def display_mode_select(self):
        log.debug(f'Select Mode: {self._modes.data["display_name"]}')
        self._hardware.get('display').clear()
        self._hardware.get('display').message(f'Select Mode\n{self._modes.data["display_name"]}')

    def enter(self):
        if self._hardware.get('switches').get('enter').state:
            self._state['enter_button_press_time'] = time.monotonic()
            log.debug(f'Enter button pressed at {self._state["enter_button_press_time"]}')
        else:
            delta = time.monotonic() - self._state['enter_button_press_time']
            self._state['enter_button_press_time'] = 0
            log.debug(f'Enter button released, held for {round(delta, 3)} seconds')
            if self._state['status'] == 'execute_complete':
                pass
            elif self._state['status'] == 'select_mode':
                log.debug('Executing Mode')
                self._state['button_lock'] = True
                self._state['status'] = 'execute_mode'
            else:
                log.warn(f'Controller in unknown status {self._state["status"]} ignoring interrupt')

    def execute_mode(self):
        log.debug(f'Executing Mode: {self._modes.data["display_name"]}')
        operations = self._modes.data.get('operations')
        for cmd, t in operations:
            log.debug(f'Cmd: {cmd}, time: {t}')
            self._mode_operation_map[cmd]()
            for i in range(0, t):
                self._hardware.get('display').clear()
                self._hardware.get('display').message(f'{cmd}\nTime Left: {t - i}')
                time.sleep(1)
        self._state['status'] = 'execute_complete'
        self._state['button_lock'] = False
        self._hardware.get('display').clear()
        self._hardware.get('display').message(f'Operations Done\nPress Enter')

    def mode(self):
        if self._hardware.get('switches').get('mode').state:
            log.debug('Button Press')
            self._state['mode_button_press_time'] = time.monotonic()
        else:
            delta = time.monotonic() - self._state['mode_button_press_time']
            self._state['mode_button_press_time'] = 0
            log.debug(f'Button Release, held for {round(delta, 3)} seconds')
            if delta >= 1.5:  # Long Press
                self._modes.previous()
            else:
                self._modes.next()
            self.display_mode_select()

    def run(self):
        log.debug(f'Execution action {self._action}')
        if self._action.lower() == 'abort':
            self.abort()
        elif self._action.lower() == 'execute_mode':
            self.execute_mode()
        elif self._state.get('button_lock', False):
            log.debug('Control Panel Lockout Enabled, ignoring button press')
        elif self._action.lower() == 'mode':
            self.mode()
        elif self._action.lower() == 'enter':
            self.enter()
        elif self._action.lower() == 'display_mode_select':
            self.display_mode_select()
        else:
            log.debug('Unknown action, ignoring')

