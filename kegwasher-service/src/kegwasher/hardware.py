# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import Adafruit_CharLCD as LCD
import logging
import RPi.GPIO as GPIO
import os

from kegwasher.exceptions import ConfigError

log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))

class Display(object):
    def init_display(self, display=dict()):
        log.debug(f'Initializing Display Driver')
        lcd = LCD.Adafruit_CharLCD(
            display.get('lcd_rs').get('pin'),
            display.get('lcd_en').get('pin'),
            display.get('lcd_d4').get('pin'),
            display.get('lcd_d5').get('pin'),
            display.get('lcd_d6').get('pin'),
            display.get('lcd_d7').get('pin'),
            display.get('lcd_columns'),
            display.get('lcd_rows'),
            display.get('lcd_bl').get('pin'))
        return lcd


class HardwareObject(object):
    def __init__(self, *args, **kwargs):
        log.debug(f'Making hardware object\t\targs: {args}\t\tkwargs: {kwargs}')
        self._name = None
        self._pin = None
        self.name = kwargs.get('name', None)
        self.pin = kwargs.get('pin', None)
        self.setup()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name=None):
        if not name:
            error_msg = f'Required attribute "name" not specified'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._name = name
        return self.name

    @property
    def pin(self):
        return self._pin

    @pin.setter
    def pin(self, pin):
        if not pin:
            error_msg = f'Required attribute "pin" not specified'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._pin = pin
        return self.pin

    def close(self):
        self.off()

    def off(self):
        log.debug(f'Setting pin {self.pin} to OFF/Low Voltage')
        GPIO.output(self.pin, 0)

    def on(self):
        log.debug(f'Setting pin {self.pin} to ON/High Voltage')
        GPIO.output(self.pin, 1)

    def open(self):
        self.on()

    def setup(self):
        log.debug(f'Setting pin {self.pin} to GPIO.OUT mode')
        GPIO.setup(self.pin, GPIO.OUT)


class Heater(HardwareObject):
    def __init__(self, *args, **kwargs):
        log.debug(f'Registering heater {kwargs.get("name", None)}')
        super(Heater, self).__init__(*args, **kwargs)


class Pump(HardwareObject):
    def __init__(self, *args, **kwargs):
        log.debug(f'Registering pump {kwargs.get("name", None)}')
        super(Pump, self).__init__(*args, **kwargs)


class Switch(HardwareObject):
    def __init__(self, *args, **kwargs):
        log.debug(f'Registering switch {kwargs.get("name", None)}')
        self._action = None
        self._event = None
        self._PUD = None
        self.action = kwargs.get('action', None)
        self.event = kwargs.get('event', None)
        self.PUD = kwargs.get('PUD', None)
        super(Switch, self).__init__(*args, **kwargs)

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, callback=None):
        if not callback:
            error_msg = f'No action defined'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._action = callback
        return self.action

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, event=None):
        if not event:
            error_msg = f'No event defined'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._event = event
        return self.event

    @property
    def PUD(self):
        return self._PUD

    @PUD.setter
    def PUD(self, PUD=None):
        if not PUD:
            error_msg = f'No PUD defined'
            log.fata(error_msg)
            raise ConfigError(error_msg)
        self._PUD = PUD
        return self.PUD

    def setup(self):
        log.debug(f'Setting pin {self.pin} to GPIO.IN mode, Pull-UP/DOWN resistor to {self.PUD}')
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=self.PUD)


class Valve(HardwareObject):
    def __init__(self, *args, **kwargs):
        log.debug(f'Registering valve {kwargs.get("name", None)}')
        super(Valve, self).__init__(*args, **kwargs)

