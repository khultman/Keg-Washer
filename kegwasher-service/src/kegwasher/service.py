# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import logging
import os
import RPi.GPIO as GPIO
import threading
import time

from kegwasher.config import *
from kegwasher.exceptions import ConfigException
from kegwasher.hardware import *
from kegwasher.linked_list import *


#  Setup Logging
logging_levels = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}
log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging_levels.get(os.getenv('LOG_LEVEL', 'INFO'), logging.INFO))


GPIO.setmode(GPIO.BCM)


class KegWasher(threading.Thread):
    def __init__(self, pin_config=None, mode_config=None):
        log.debug(f'Initializing KegWasher')
        threading.Thread.__init__(self)
        self._switch_callbacks = {
            'sw_abort': self.sw_abort,
            'sw_enter': self.sw_enter,
            'sw_mode': self.sw_mode,
            'sw_nc': self.sw_nc
        }
        self._status_map = {
            'initialize': self.__init__,
            'select_mode': self.select_mode,
            'aborted': self.aborted_mode,
        }
        self._mode_map = {
            'air_fill_closed': self.air_fill_closed,
            'air_fill_open': self.air_fill_open,
            'clean_closed': self.clean_closed,
            'clean_open': self.clean_open,
            'cleaner_fill': self.cleaner_fill,
            'co2_fill_closed': self.co2_fill_closed,
            'co2_fill_open': self.co2_fill_open,
            'drain': self.drain,
            'rinse': self.rinse,
            'sanitize': self.sanitize,
            'sanitizer_fill': self.sanitizer_fill
        }
        self._modes = None
        self._aborted = False
        self._button_lock = False
        self._enabled_loop = True
        self._enter_button_press_time = 0
        self._mode_button_press_time = 0
        self._status = 'initialize'
        self._threads = []
        #
        self._validate_hardware_config(pin_config)
        self._pin_config = pin_config
        self._display = Display().init_display(pin_config.get('display'))
        self._display.clear()
        self._display.message(f'Initializing....\nPlease.Standby..')
        self._heaters = self._init_heaters(pin_config.get('heaters'))
        self._pumps = self._init_pumps(pin_config.get('pumps'))
        self._valves = self._init_valves(pin_config.get('valves'))
        self._switches = self._init_switches(pin_config.get('switches'))
        self._init_modes(mode_config)

    def _init_heaters(self, heaters=list()):
        log.debug(f'Initializing heaters')
        configured_heaters = dict()
        for heater in heaters:
            if not heater.get('name', None) and not heater.get('pin', None):
                error_msg = f'Missing correct heater configuration {heater}'
                log.fatal(error_msg)
                raise ConfigException(error_msg)
            configured_heaters[heater.get('name')] = Heater(**heater)
        return configured_heaters

    def _init_modes(self, modes=None):
        log.debug(f'Creating circular doubly linked list from defined modes')
        self._modes = CircularDoublyLinkedList()
        for mode, data in modes.items():
            self._modes.append(Node(data))

    def _init_pumps(self, pumps=list()):
        log.debug(f'Initializing pumps')
        configured_pumps = dict()
        for pump in pumps:
            if not pump.get('name', None) and not pump.get('pin', None):
                error_msg = f'Missing correct pump configuration {pump}'
                log.fatal(error_msg)
                raise ConfigException(error_msg)
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
                    and not switch.get('callback', None):
                error_msg = f'Invalid switch configuration: {switch}'
                log.fatal(error_msg)
                raise ConfigException(error_msg)
            log.debug(f'Initializing Switch: {switch.get("name")}')
            GPIO.setup(switch.get('pin', 0), GPIO.IN, pull_up_down=switch.get('PUD', GPIO.PUD_DOWN))
            log.debug(f'Configuring event detection for {switch.get("name")}, callback: {switch.get("callback")}')
            GPIO.add_event_detect(switch.get('pin', 0),
                                  switch.get('event', GPIO.BOTH),
                                  self._switch_callbacks.get(switch.get('callback', 'sw_nc'), self.sw_nc))
            configured_switches[switch.get('name')] = switch
        return configured_switches

    def _init_valves(self, valves=list()):
        log.debug(f'Initializing valves')
        configured_valves = dict()
        for valve in valves:
            if not valve.get('name', None) and not valve.get('pin', None):
                error_msg = f'Missing valve configuration: {valve}'
                log.fatal(error_msg)
                raise Exception(error_msg)
            configured_valves[valve.get('name')] = Valve(**valve)
        return configured_valves

    def _validate_hardware_config(self, pin_config=None):
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

    def _all_heaters_off(self):
        log.debug(f'Turning all heaters off')
        for heater in self._heaters.keys():
            self._heaters.get(heater).off()

    def _all_pumps_off(self):
        log.debug(f'Turning all pumps off')
        for pump in self._pumps.keys():
            self._pumps.get(pump).off()

    def _all_valves_closed(self):
        log.debug(f'Closing all valves')
        for valve in self._valves.keys():
            self._valves.get(valve).close()

    def _all_off_closed(self):
        log.debug(f'Turning off all devices, closing all valves')
        self._all_pumps_off()
        self._all_heaters_off()
        self._all_valves_closed()

    def air_fill_closed(self):
        log.debug('Setting state to air_fill_closed')
        self._all_off_closed()
        self._valves['air_in'].open()

    def air_fill_open(self):
        log.debug('Setting state to air_fill_open')
        self._all_off_closed()
        self._valves.get('air_in').open()
        self._valves.get('waste_out').open()

    def clean_closed(self):
        log.debug('Setting state to clean_closed')
        self._all_off_closed()
        for valve in ['cleaner_in', 'cleaner_rtn', 'pump_in', 'pump_out']:
            self._valves.get(valve).open()
        self._pumps.get('pump_1').on()
        self._heaters.get('heater_1').on()

    def clean_open(self):
        log.debug('Setting state to clean_open')
        self._all_off_closed()
        for valve in ['cleaner_in', 'waste_out', 'pump_in', 'pump_out']:
            self._valves.get(valve).open()
        self._pumps.get('pump_1').on()
        self._heaters.get('header_1').on()

    def cleaner_fill(self):
        log.debug('Setting state to cleaner_fill')
        self._all_off_closed()
        for valve in ['water_in', 'cleaner_in']:
            self._valves.get(valve).open()

    def co2_fill_closed(self):
        log.debug('Setting state to co2_fill_closed')
        self._all_off_closed()
        self._valves.get('co2_in').open()

    def co2_fill_open(self):
        log.debug('Setting state to co2_fill_open')
        self._all_off_closed()
        self._valves.get('co2_in').open()
        self._valves.get('waste_out').open()

    def drain(self):
        log.debug('Setting state to drain')
        self._all_off_closed()
        self._valves.get('waste_out').open()
        self._valves.get('air_in').open()

    def rinse(self):
        log.debug('Setting state to rinse')
        self._all_off_closed()
        for valve in ['water_in', 'pump_in', 'pump_out', 'waste_out']:
            self._valves.get(valve).open()
        self._pumps.get('pump_1').on()
        self._heaters.get('heater_1').on()

    def sanitize(self):
        log.debug('Setting state to sanitize')
        self._all_off_closed()
        for valve in ['sanitizer_in', 'pump_in', 'pump_out', 'waste_out']:
            self._valves.get(valve).open()
        self._pumps.get('pump_1').on()
        self._heaters.get('heater_1').on()

    def sanitizer_fill(self):
        log.debug('Setting state to santizer fill')
        self._all_off_closed()
        for valve in ['water_in', 'sanitizer_in']:
            self._valves.get(valve).open()

    def aborted_mode(self):
        log.debug(f'Aborted\nPress Enter')
        self._display.clear()
        self._display.message(f'Aborted\nPress Enter')

    def select_mode(self):
        log.debug(f'Select Mode: {self._modes.data["display_name"]}')
        self._display.clear()
        self._display.message(f'Select Mode\n{self._modes.data["display_name"]}')

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

    def sw_abort(self, *args, **kwargs):
        log.debug(f'ABORT Latch Released: received args {args} ;; received kwargs {kwargs}')
        self._all_off_closed()
        self._button_lock = False
        self.update_status('aborted', 1)

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

    def sw_mode(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        log.debug(f'MODE Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')
        if self._button_lock:
            log.debug(f'Button lockout enabled, ignoring')
            return
        if fall_rise:  # Button Pressed
            self._mode_button_press_time = time.monotonic()
        else:  # Button Released
            cur_time = time.monotonic()
            orig_time = self._mode_button_press_time
            self._mode_button_press_time = cur_time
            delta_time = cur_time - orig_time
            if delta_time >= 3:
                log.debug('Previous Mode')
                self._modes.previous()
            elif delta_time >= 0.07:
                log.debug('Next Mode')
                self._modes.next()
            else:
                log.debug('Caught a bounce')
        self.update_status('select_mode', 1)

    def sw_nc(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        log.debug(f'Not Connected Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')

    def update_status(self, status=None, force=0):
        if status == self._status and not force:
            log.debug('No status change, not refreshing display')
            return
        if status in self._status_map:
            log.debug(f'Updating status to {status} - force: {force}')
            self._status = status
            self._status_map[status]()

    def run(self):
        log.debug('Pre-infinite run loop')
        self.update_status('select_mode')
        log.debug('Entering Infinite Loop Handler')
        try:
            while self._enabled_loop:
                time.sleep(1e6)

        except KeyboardInterrupt:
            self._display.clear()
            GPIO.cleanup()

