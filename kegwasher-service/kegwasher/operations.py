# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import logging
import os

from kegwasher.exceptions import ConfigError

log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))


class Operations(object):
    def __init__(self, *args, **kwargs):
        self._hardware = kwargs.get('hardware', None)
        if not self._hardware:
            error_msg = f'Hardware configuration not provided'
            log.fatal(error_msg)
            raise ConfigError(error_msg)

    def heaters_off(self, *args):
        for heater in args:
            log.debug(f'Requesting {heater} heater state to off')
            self._hardware.get('heaters').get(heater).off()

    def heaters_on(self, *args):
        for heater in args:
            log.debug(f'Requesting {heater} heater state to on')
            self._hardware.get('heaters').get(heater).on()

    def pumps_off(self, *args):
        for pump in args:
            log.debug(f'Requesting {pump} pump state to off')
            self._hardware.get('pumps').get(pump).off()

    def pumps_on(self, *args):
        for pump in args:
            log.debug(f'Requesting {pump} pump state to on')
            self._hardware.get('pumps').get(pump).on()

    def valves_close(self, *args):
        for valve in args:
            log.debug(f'Requesting {valve} valve state to closed')
            self._hardware.get('valves').get(valve).close()

    def valves_open(self, *args):
        for valve in args:
            log.debug(f'Requesting {valve} valve state to open')
            self._hardware.get('valves').get(valve).open()

    def all_heaters_off(self):
        log.debug(f'Requesting all heaters off')
        self.heaters_off(*self._hardware.get('heaters').keys())

    def all_pumps_off(self):
        log.debug(f'Requesting all pumps off')
        self.pumps_off(*self._hardware.get('pumps').keys())

    def all_valves_closed(self):
        log.debug(f'Requisting all valves closed')
        self.valves_close(*self._hardware.get('valves').keys())

    def all_off_closed(self):
        log.debug(f'Requesting all devices off, all valves closed')
        self.all_pumps_off()
        self.all_heaters_off()
        self.all_valves_closed()

    def air_fill_closed(self):
        log.debug('Operation state air_fill_closed')
        self.all_off_closed()
        self.valves_open('air_in')

    def air_fill_open(self):
        log.debug('Operation state air_fill_open')
        self.all_off_closed()
        self.valves_open('air_in', 'waste_out')

    def clean_closed(self):
        log.debug('Operation state clean_closed')
        self.all_off_closed()
        self.valves_open('cleaner_in', 'cleaner_rtn', 'pump_in', 'pump_out')
        self.pumps_on('pump_1')
        self.heaters_on('heater_1')

    def clean_open(self):
        log.debug('Operation state clean_open')
        self.all_off_closed()
        self.valves_open('cleaner_in', 'waste_out', 'pump_in', 'pump_out')
        self.pumps_on('pump_1')
        self.heaters_on('header_1')

    def cleaner_fill(self):
        log.debug('Operation state cleaner_fill')
        self.all_off_closed()
        self.valves_open('water_in', 'cleaner_in')

    def co2_fill_closed(self):
        log.debug('Operation state co2_fill_closed')
        self.all_off_closed()
        self.valves_open('co2_in')

    def co2_fill_open(self):
        log.debug('Operation state co2_fill_open')
        self.all_off_closed()
        self.valves_open('co2_in', 'waste_out')

    def drain(self):
        log.debug('Operation state drain')
        self.all_off_closed()
        self.valves_open('waste_out', 'air_in')

    def rinse(self):
        log.debug('Operation state rinse')
        self.all_off_closed()
        self.valves_open('water_in', 'pump_in', 'pump_out', 'waste_out')
        self.pumps_on('pump_1')
        self.heaters_on('heater_1')

    def sanitize(self):
        log.debug('Operation state sanitize')
        self.all_off_closed()
        self.valves_open('sanitizer_in', 'pump_in', 'pump_out', 'waste_out')
        self.pumps_on('pump_1')
        self.heaters_on('heater_1')

    def sanitizer_fill(self):
        log.debug('Operation state santizer_fill')
        self.all_off_closed()
        self.valves_open('water_in', 'sanitizer_in')
