# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import logging
import smbus2

from kegwasher.exceptions import ConfigError

log = logging.getLogger(os.getenv('LOGGER_NAME', 'kegwasher'))


class pca955x(object):
    def __init__(self, *args, **kwargs):
        self._ports = {
            'INPUT_PORT': 0,
            'OUTPUT_PORT': 1,
            'POLARITY_PORT': 2,
            'CONFIG_PORT': 3
        }
        #
        self._address = None
        self._bus = None
        self._direction = None
        self._gpios = None
        self._outputvalue = None
        #
        self.address = kwargs.get('address', None)
        self.bus = kwargs.get('bus', None)
        self.gpios = kwargs.get('gpios', None)
        # Create i2c bus interface
        self._smbus = smbus2.SMBus(self.bus)
        #
        self.direction = self._readport(self._ports['CONFIG_PORT'])
        self.outputvalue = self._readport(self._ports['OUTPUT_PORT'])

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address=None):
        if not 0x20 <= address <= 0x27:
            error_msg = f'Address out of range, expecting between 0x20 and 0x27, received {address}'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._address = address

    @property
    def bus(self):
        return self._bus

    @bus.setter
    def bus(self, bus=None):
        if not 0 <= bus <= 255:
            error_msg = f'I2C Bus Invalid, expecting int between 0 and 255, received {bus}'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._bus = bus

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction=None):
        if not direction:
            error_msg = "Expecting chip direction data, received null"
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._direction = direction

    @property
    def gpios(self):
        return self._gpios

    @gpios.setter
    def gpios(self, gpios=None):
        if not 0 <= gpios <= 16:
            error_msg = f'The number of GPIO pins must be between 0 and 16, received {gpios}'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._gpios = gpios

    @property
    def outputvalue(self):
        return self._outputvalue

    @outputvalue.setter
    def outputvalue(self, outputvalue=None):
        if not outputvalue:
            error_msg = f'Expecting chip output value data, received null'
            log.fatal(error_msg)
            raise ConfigError(error_msg)
        self._outputvalue = outputvalue

    def _bitchange(self, bitmap, bit, value):
        if not 0 <= value <= 1:
            error_msg = f'Expecting 0 or 1 for bit value, received: {value}'
            log.fatal(error_msg)
            raise Exception(error_msg)
        if not value:
            return bitmap & ~(1 << bit)
        return bitmap | (1 << bit)

    def _changepin(self, port, pin, value):
        bits = self._bitchange(self._readpin(port, pin), pin, value)
        if self.gpios > 8:
            self._smbus.write_word_data(self.address, port << 1, bits)
        else:
            self._smbus.write_byte_data(self.address, port, bits)
        return bits

    def _readpin(self, port, pin):
        if not 0 <= pin <= self.gpios:
            error_msg = f'Expecting pin value between 0 and {self.gpios}, received: {pin}'
            log.fatal(error_msg)
            raise Exception(error_msg)
        if self.gpios > 8:
            return self._smbus.read_word_data(self.address, port << 1)
        return self._smbus.read_byte_data(self.address, port)

    def _readport(self, port):
        if self.gpios > 8:
            return self._smbus.read_word_data(self.address, port << 1)
        return self._smbus.read_byte_data(self.address, port)

    def config(self, pin, mode):
        self.direction = self._changepin(self._ports['CONFIG_PORT'], pin, mode)
        return self.direction

    def input(self, pin):
        if not self.direction & (1 << pin) == 0:
            error_msg = f'Pin {pin} is not set to input'
            log.critical(error_msg)
            raise IOError(error_msg)
        return self._readpin(self._ports['INPUT_PORT'], pin) & (1 << pin)

    def output(self, pin, value):
        if self.direction & (1 << pin) == 0:
            error_msg = f'Pin {pin} is not set to output'
            log.critical(error_msg)
            raise IOError(error_msg)
        return self._changepin(self._ports['OUTPUT_PORT'], pin, value)

    def polarity(self, pin, value):
        return self._changepin(self._ports['POLARITY_PORT'], pin, value)

    def setmode(self, mode):
        pass

    def setup(self, pin, mode):
        self.config(pin, mode)







