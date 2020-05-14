# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>
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

    def abort(self):
        if self._state['aborted'] and self._hardware.get('switches').get('abort').state:
            log.debug(f'Already Aborted, passing')
            pass
        elif not self._hardware.get('switches').get('abort').state:
            log.debug(f'Abort switch reset, resuming operation')
            self._state['aborted'] = False
        else:
            log.debug(f'Aborting')
            self._operations.all_off_closed()
            self._state['aborted'] = True
            self._hardware.get('display').clear()
            self._hardware.get('display').message(f'Aborted\nReset Controller')
            for t in self._threads:
                t.abort()
                self._threads.remove(t)

    def display_mode_select(self):
        log.debug(f'Select Mode: {self._modes.data["display_name"]}')
        self._hardware.get('display').clear()
        self._hardware.get('display').message(f'Select Mode\n{self._modes.data["display_name"]}')

    def enter(self):
        if self._hardware.get('switches').get('enter').state:
            self._state['enter_button_press_time'] = time.monotonic
            log.debug(f'Enter button pressed at {self._state["enter_button_press_time"]}')
        else:
            delta = time.monotonic() - self._state['enter_button_press_time']
            self._state['enter_button_press_time'] = 0
            log.debug(f'Enter button released, held for {round(delta, 3)} seconds')
            if self._state['aborted']:
                self._state['aborted'] = False
            else:
                log.debug('Executing Mode')
                self._state['button_lock'] = True

    def execute_mode(self):
        log.debug(f'Executing Mode: {self._modes.data["display_name"]}')
        operations = self._modes.data.get('operations')
        for cmd, t in operations:
            log.debug(f'Cmd: {cmd}, time: {t}')
            self._mode_operation_map[cmd]()
            for i in range(0, t):
                self._display.clear()
                self._display.message(f'{cmd}\nTime Left: {t - i}')
                time.sleep(1)

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

    def sw_enter(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        log.debug(f'ENTER Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')
        if self._aborted:
            log.debug(f'Resetting abort state')
            self._aborted = False
            self.update_status('select_mode')
            return
        if self._button_lock:
            log.debug(f'Button lockout enabled, ignoring')
            return
        t = threading.Thread(target=self.execute_mode())
        t.daemon = False
        self._threads.append(t)
        t.start()

    def update_status(self, status=None, force=0):
        if status == self._status and not force:
            log.debug('No status change, not refreshing display')
            return
        if status in self._status_map:
            log.debug(f'Updating status to {status} - force: {force}')
            self._status = status
            self._status_map[status]()