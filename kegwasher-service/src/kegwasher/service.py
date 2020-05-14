# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import logging
import os
import RPi.GPIO as GPIO
import threading
import time

from kegwasher.actions import Action
from kegwasher.config import pin_config, mode_config
from kegwasher.exceptions import AbortException, ConfigError
from kegwasher.hardware import *
from kegwasher.linked_list import *
from kegwasher.operations import Operations


log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))

GPIO.setmode(GPIO.BCM)


class KegWasher(threading.Thread):
    def __init__(self, pin_config=None, mode_config=None):
        log.debug(f'Initializing KegWasher')
        threading.Thread.__init__(self)
        # self._status_map = {
        #     'initialize': self.__init__,
        #     'select_mode': self.select_mode,
        #     'aborted': self.aborted_mode,
        # }
        #
        self._state = {
            'aborted': False,
            'alive': True,
            'button_lock': False,
            'enter_button_press_time': 0,
            'mode_button_press_time': 0,
            'status': 'initialize'
        }
        self._threads = list()
        #
        self._pin_config = self._validate_hardware_config(pin_config)
        self._hardware = dict()
        self._hardware['display'] = Display().init_display(pin_config.get('display'))
        self._hardware.get('display').clear()
        self._hardware.get('display').message(f'Initializing....\nPlease.Standby..')
        self._hardware['heaters'] = self._init_heaters(pin_config.get('heaters'))
        self._hardware['pumps'] = self._init_pumps(pin_config.get('pumps'))
        self._hardware['valves'] = self._init_valves(pin_config.get('valves'))
        self._hardware['switches'] = self._init_switches(pin_config.get('switches'))
        self._operations = Operations(hardware=self._hardware)
        self._operations.all_off_closed()
        #
        self._modes = self._init_modes(mode_config)

    @staticmethod
    def _init_heaters(heaters=list()):
        log.debug(f'Initializing heaters')
        configured_heaters = dict()
        for heater in heaters:
            if not heater.get('name', None) and not heater.get('pin', None):
                error_msg = f'Missing correct heater configuration {heater}'
                log.fatal(error_msg)
                raise ConfigError(error_msg)
            configured_heaters[heater.get('name')] = Heater(**heater)
        return configured_heaters

    @staticmethod
    def _init_modes(modes=None):
        log.debug(f'Creating circular doubly linked list from defined modes')
        cdll = CircularDoublyLinkedList()
        for mode, data in modes.items():
            cdll.append(Node(data))
        return cdll

    @staticmethod
    def _init_pumps(pumps=list()):
        log.debug(f'Initializing pumps')
        configured_pumps = dict()
        for pump in pumps:
            if not pump.get('name', None) and not pump.get('pin', None):
                error_msg = f'Missing correct pump configuration {pump}'
                log.fatal(error_msg)
                raise ConfigError(error_msg)
            configured_pumps[pump.get('name')] = Pump(**pump)
        return configured_pumps

    def _init_switches(self, switches=list()):
        log.debug(f'Initializing switches')
        configured_switches = dict()
        for switch in switches:
            if not switch.get('name', None) \
                    and not switch.get('pin', None) \
                    and not switch.get('PUD', None) \
                    and not switch.get('event', None) \
                    and not switch.get('action', None):
                error_msg = f'Invalid switch configuration: {switch}'
                log.fatal(error_msg)
                raise ConfigError(error_msg)
            pin = switch.get('pin')
            name = switch.get('name')
            switch_object = Switch(**switch)
            configured_switches[pin] = switch_object
            configured_switches[name] = switch_object
            log.debug(f'Configuring event detection for {switch.get("name")}, action: {switch.get("action")}')
            GPIO.add_event_detect(pin, configured_switches[pin].event, self.sw_interrupt_handler, 100)
        return configured_switches

    @staticmethod
    def _init_valves(valves=list()):
        log.debug(f'Initializing valves')
        configured_valves = dict()
        for valve in valves:
            if not valve.get('name', None) and not valve.get('pin', None):
                error_msg = f'Missing valve configuration: {valve}'
                log.fatal(error_msg)
                raise Exception(error_msg)
            configured_valves[valve.get('name')] = Valve(**valve)
        return configured_valves

    @staticmethod
    def _validate_hardware_config(pin_config=None):
        log.debug(f'Validating hardware configuration')
        if not (pin_config and
                pin_config.get('display', None) and
                pin_config.get('heaters', None) and
                pin_config.get('pumps') and
                pin_config.get('switches') and
                pin_config.get('valves')):
            error_msg = f'Invalid Hardware Configuration Received: {pin_config}'
            log.fatal(error_msg)
            raise Exception(error_msg)
        return pin_config

    def sw_interrupt_handler(self, *args):
        log.debug(f'Switch Interrupt Handler received event for pin {args[0]}')
        t = Action(**{'action': self._hardware.get('switches').get(args[0]).action,
                       'hardware': self._hardware,
                       'modes': self._modes,
                       'operations': self._operations,
                       'state': self._state,
                       'threads': self._threads})
        t.daemon = False
        t.start()
        self._threads.append(t)

    def run(self):
        log.debug('Entering Infinite Loop Handler')
        try:
            while self._state.get('alive', False):
                if self._state.get('aborted', False):
                    time.sleep(1)
                else:
                    if len(self._threads) >= 1:
                        for t in self._threads:
                            if t.is_alive():
                                t.join(timeout=0.01)
                            if not t.is_alive():
                                log.debug('Reaping thread')
                                self._threads.remove(t)
                    if self._state['status'] == 'execute_mode' or self._state['status'] == 'initialize':
                        act = self._state['status']
                        if self._state['status'] == 'execute_mode':
                            self._state['status'] = 'executing'
                        if self._state['status'] == 'initialize':
                            act = 'display_mode_select'
                            self._state['status'] = 'select_mode'
                        self._state['status'] = 'executing'
                        t = Action(**{'action': act,
                                      'hardware': self._hardware,
                                      'modes': self._modes,
                                      'operations': self._operations,
                                      'state': self._state,
                                      'threads': self._threads})
                        t.daemon = False
                        t.start()
                        self._threads.append(t)
                    time.sleep(0.01)
        except KeyboardInterrupt:
            log.info('Received Keyboard Interrupt')
            self._display.clear()
            self._operations.all_off_closed()
            GPIO.cleanup()


if __name__ == '__main__':
    keg_washer = KegWasher(pin_config, mode_config)
    keg_washer.daemon = True
    keg_washer.start()
    keg_washer.join()

