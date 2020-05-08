# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import Adafruit_CharLCD as LCD
import logging
import os
import RPi.GPIO as GPIO
import time


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

# Hardware Configuration
pin_config = {
    'display': {
        'lcd_rs': {'pin': 16},
        'lcd_en': {'pin': 19},
        'lcd_d4': {'pin': 7},
        'lcd_d5': {'pin': 8},
        'lcd_d6': {'pin': 10},
        'lcd_d7': {'pin': 9},
        'lcd_bl': {'pin': 0},
        'lcd_columns': 16,
        'lcd_rows': 2
    },
    'pumps': {
        'pump_1': {'pin': 27}
    },
    'switches': {
        'sw_mode': {'pin': 5, 'PUD': GPIO.PUD_DOWN, 'event': GPIO.FALLING, 'callback': 'sw_mode'},
        'sw_enter': {'pin': 6, 'PUD': GPIO.PUD_DOWN, 'event': GPIO.FALLING, 'callback': 'sw_enter'},
        'sw_3': {'pin': 12, 'PUD': GPIO.PUD_DOWN, 'event': GPIO.FALLING, 'callback': 'sw_nc'},
        'sw_4': {'pin': 13, 'PUD': GPIO.PUD_DOWN, 'event': GPIO.FALLING, 'callback': 'sw_nc'},
        'sw_abort': {'pin': 20, 'PUD': GPIO.PUD_DOWN, 'event': GPIO.RISING, 'callback': 'sw_abort'}
    },
    'valves': {
        'cleaner_in': {'pin': 21},
        'sanitizer_in': {'pin': 26},
        'water_in': {'pin': 4},
        'pump_in': {'pin': 17},
        'co2_in': {'pin': 18},
        'air_in': {'pin': 22},
        'cleaner_rtn': {'pin': 23},
        'pump_out': {'pin': 24},
        'waste_out': {'pin': 25}
    }
}


class KegWasher(object):
    def __init__(self, pin_config=None):
        log.debug(f'Initializing KegWasher')
        self._switch_callbacks = {
            'sw_abort': self.sw_abort,
            'sw_enter': self.sw_enter,
            'sw_mode': self.sw_mode,
            'sw_nc': self.sw_nc
        }
        self._validate_hardware(pin_config)
        self._pin_config = pin_config
        self._init_display()
        self._lcd.clear()
        self._lcd.message(f'Initializing....\nPlease.Standby..')
        self._init_pumps()
        self._init_valves()
        self._init_switches()

    def _init_display(self):
        self._lcd = LCD.Adafruit_CharLCD(
            self._pin_config.get('display', dict()).get('lcd_rs').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_en').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_d4').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_d5').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_d6').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_d7').get('pin'),
            self._pin_config.get('display', dict()).get('lcd_columns'),
            self._pin_config.get('display', dict()).get('lcd_rows'),
            self._pin_config.get('display', dict()).get('lcd_bl').get('pin'))

    def _init_pumps(self):
        for pump_name, pump_settings in self._pin_config['pumps'].items():
            log.debug(f'Setting pump {pump_name} on pin {pump_settings.get("pin", "Undefined")} to {GPIO.OUT} mode')
            GPIO.setup(pump_settings.get("pin", 0), GPIO.OUT)
            log.debug(f'Setting pump {pump_name} on pin {pump_settings.get("pin", "Undefined")} to OFF')
            GPIO.output(pump_settings.get('pin', 0), 0)

    def _init_switches(self):
        for switch_name, switch_settings in self._pin_config['switches'].items():
            log.debug(f'Intializing Switch: {switch_name}')
            GPIO.setup(switch_settings.get('pin', 0), GPIO.IN, pull_up_down=switch_settings.get('PUD', GPIO.PUD_UP))
            log.debug(f'Configuring event detection for {switch_name}, callback: {switch_settings["callback"]}')
            GPIO.add_event_detect(switch_settings.get('pin', 0),
                                  switch_settings.get('event', GPIO.BOTH),
                                  self._switch_callbacks.get(switch_settings.get('callback', 'sw_nc'), self.sw_nc))

    def _init_valves(self):
        for valve_name, valve_settings in self._pin_config['valves'].items():
            log.debug(f'Setting valve {valve_name} on pin {valve_settings.get("pin", "Undefined")} to {GPIO.OUT} mode')
            GPIO.setup(valve_settings.get("pin", 0), GPIO.OUT)
            log.debug(f'Setting valve {valve_name} on pin {valve_settings.get("pin", "Undefined")} to CLOSED')
            GPIO.output(valve_settings.get("pin", 0), 0)

    def _validate_hardware(self, pin_config=None):
        log.debug(f'Hardware raw object: {pin_config}')
        if not (pin_config and
                pin_config.get('display', None) and
                pin_config.get('pumps') and
                pin_config.get('switches') and
                pin_config.get('valves')):
            error_msg = f'Invalid Hardware Configuration Received: {pin_config}'
            log.fatal(error_msg)
            raise Exception(error_msg)

    def sw_abort(self, pin):
        log.debug(f'ABORT Latch Released; pin {pin} received an interrupt')

    def sw_enter(self, pin):
        log.debug(f'ENTER Button press: pin {pin} received an interrupt')

    def sw_mode(self, pin):
        log.debug(f'MODE Button press, pin {pin} received an interrupt')

    def sw_nc(self, pin):
        log.debug(f'Not Connected Button press, pin {pin} received an interrupt')

    def run(self):
        log.debug('Entering Infinite Loop Handler')
        try:
            while True:
                time.sleep(200)

        except KeyboardInterrupt:
            GPIO.cleanup()



if __name__ == '__main__':
    try:
        keg_washer = KegWasher(pin_config)
        keg_washer.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
    GPIO.cleanup()
