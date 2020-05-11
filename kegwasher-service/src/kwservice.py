# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import Adafruit_CharLCD as LCD
import logging
import os
import RPi.GPIO as GPIO
import time


# Mode Configuration
# Available Mode Operations
# air_fill_closed   - Fill keg with air, all other valves closed
# air_fill_open     - Fill keg with air, waste_out valve open
# clean_closed      - Closed loop clean: cleaner_in, cleaner_rtn & pump valves open, pump on
# clean_open        - Open loop clean: cleaner_in, waste_out & pump valves open, pump on
# co2_fill_closed   - Fill keg with CO2, all other valves closed
# co2_fill_open     - Fill keg with CO2, waste_out valve open
# drain             - waste_out valve open, all other valves closed
# rinse             - water_in, waste_out & pump valves open, pump on
# sanitize          - sanitizer_in, waste_out & pump valves open, pump on
mode_config = {
    'clean': {
        'display_name': 'Clean',
        'operations': [
            #  Operation         Time to Run Operation
            ('air_fill_open',    30),
            ('rinse',            300),
            ('air_fill_open',    10),
            ('drain',            30),
            ('clean_open',       30),
            ('clean_closed',     300),
            ('air_fill_open',    10),
            ('drain',            30),
            ('rinse',            60),
            ('co2_fill_open',    10),
            ('drain',            30),
            ('sanitize',         120),
            ('co2_fill_open',    10),
            ('drain',            30),
            ('co2_fill_open',    5),
            ('co2_fill_closed',  25)
        ]
    },
    'deep_clean': {
        'display_name': 'Deep Clean',
        'operations': [
            #  Operation         Time to Run Operation
            ('air_fill_open',    30),
            ('air_fill_closed',  10),
            ('drain',            30),
            ('rinse',            300),
            ('air_fill_open',    10),
            ('drain',            30),
            ('clean_open',       30),
            ('clean_closed',     300),
            ('air_fill_open',    10),
            ('drain',            30),
            ('rinse',            60),
            ('clean_open',       30),
            ('clean_closed',     300),
            ('drain',            30),
            ('co2_fill_open',    10),
            ('rinse',            60),
            ('co2_fill_open',    10),
            ('drain',            30),
            ('sanitize',         120),
            ('co2_fill_open',    10),
            ('drain',            30),
            ('co2_fill_open',    5),
            ('co2_fill_closed',  25)
        ]
    },
    'sanitize': {
        'display_name': 'Sanitize',
        'operations': [
            #  Operation         Time to Run Operation
            ('co2_fill_closed',  5),
            ('co2_fill_open',    5),
            ('drain',            30),
            ('sanitize',         120),
            ('co2_fill_open',    10),
            ('drain',            30),
            ('co2_fill_open',    5),
            ('co2_fill_closed',  25)
        ]
    },
    'rinse_empty': {
        'display_name': 'Rinse & Empty',
        'operations': [
            #  Operation         Time to Run Operation
            ('air_fill_open',    30),
            ('air_fill_closed',  10),
            ('drain',            30),
            ('rinse',            300),
            ('air_fill_open',    10),
            ('drain',            60),
        ]
    }
}

# Hardware Configuration
pin_config = {
    'display': {
        'lcd_rs':       {'pin': 16},
        'lcd_en':       {'pin': 19},
        'lcd_d4':       {'pin': 7},
        'lcd_d5':       {'pin': 8},
        'lcd_d6':       {'pin': 10},
        'lcd_d7':       {'pin': 9},
        'lcd_bl':       {'pin': 0},
        'lcd_columns':  16,
        'lcd_rows':     2
    },
    'pumps': {
        'pump_1':       {'pin': 27}
    },
    'switches': {
        'sw_mode':      {'pin': 5,     'PUD': GPIO.PUD_DOWN,    'event': GPIO.BOTH,       'callback': 'sw_mode'},
        'sw_enter':     {'pin': 6,     'PUD': GPIO.PUD_DOWN,    'event': GPIO.BOTH,       'callback': 'sw_enter'},
        'sw_3':         {'pin': 12,    'PUD': GPIO.PUD_DOWN,    'event': GPIO.BOTH,       'callback': 'sw_nc'},
        'sw_4':         {'pin': 13,    'PUD': GPIO.PUD_DOWN,    'event': GPIO.BOTH,       'callback': 'sw_nc'},
        'sw_abort':     {'pin': 20,    'PUD': GPIO.PUD_DOWN,    'event': GPIO.RISING,     'callback': 'sw_abort'}
    },
    'valves': {
        'cleaner_in':   {'pin': 21},
        'sanitizer_in': {'pin': 26},
        'water_in':     {'pin': 4},
        'pump_in':      {'pin': 17},
        'co2_in':       {'pin': 18},
        'air_in':       {'pin': 22},
        'cleaner_rtn':  {'pin': 23},
        'pump_out':     {'pin': 24},
        'waste_out':    {'pin': 25}
    }
}


########################################################################################################################
########################################################################################################################
########################################### END USER CONFIGURATION #####################################################
########################################################################################################################
########################################################################################################################

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


class CleaningMode(object):
    def __init__(self, data):
        self.data = data
        self.next = None
        self.previous = None


class ModeList(object):
    def __init__(self):
        self.head = None
        
    @property
    def data(self):
        cur_node = self.head
        if cur_node is None:
            return None
        return cur_node.data

    def get_node(self, index):
        cur_node = self.head
        for i in range(index):
            cur_node = cur_node.next
            if cur_node == self.head:
                return None
            return cur_node

    def insert_after(self, ref_node, new_node):
        new_node.previous = ref_node
        new_node.next = ref_node.next
        new_node.next.previous = new_node
        ref_node.next = new_node

    def insert_before(self, ref_node, new_node):
        self.insert_after(ref_node.previous, new_node)

    def append(self, new_node=None):
        if self.head is None:
            new_node.next = new_node
            new_node.previous = new_node
            self.head = new_node
        else:
            self.insert_after(self.head.previous, new_node)

    def push(self, new_node=None):
        self.append(new_node)
        self.head = new_node

    def next(self):
        self.head = self.head.next

    def previous(self):
        self.head = self.head.previous


class KegWasher(object):
    def __init__(self, pin_config=None, mode_config=None):
        log.debug(f'Initializing KegWasher')
        self._switch_callbacks = {
            'sw_abort': self.sw_abort,
            'sw_enter': self.sw_enter,
            'sw_mode': self.sw_mode,
            'sw_nc': self.sw_nc
        }
        self._modes = None
        self._button_lock = 0
        self._mode_button_press_time = 0
        self._enter_button_press_time = 0
        self._validate_hardware(pin_config)
        self._pin_config = pin_config
        self._init_display()
        self._lcd.clear()
        self._lcd.message(f'Initializing....\nPlease.Standby..')
        self._init_pumps()
        self._init_valves()
        self._init_switches()
        self._init_modes(mode_config)

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

    def _init_modes(self, modes=None):
        self._modes = ModeList()
        for mode, data in modes.items():
            self._modes.append(CleaningMode(data))

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

    def sw_abort(self, *args, **kwargs):
        log.debug(f'ABORT Latch Released: received args {args} ;; received kwargs {kwargs}')

    def sw_enter(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        log.debug(f'ENTER Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')

    def sw_mode(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        if fall_rise:  # Button Pressed
            self._mode_button_press_time = time.monotonic()
        else:  # Button Released
            cur_time = time.monotonic()
            orig_time = self._mode_button_press_time
            self._mode_button_press_time = cur_time
            delta_time = cur_time - orig_time
            if delta_time >= 3.5:
                log.debug('Previous Mode')
                self._modes.previous()
            elif delta_time >= 0.05:
                log.debug('Next Mode')
                self._modes.next()
            else:
                log.debug('Caught a bounce')
        log.debug(f'MODE Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')

    def sw_nc(self, *args, **kwargs):
        fall_rise = GPIO.input(args[0])
        log.debug(f'Not Connected Button press: received args {args} ;; received kwargs {kwargs} ;; fall_rise {fall_rise}')

    def run(self):
        log.debug('Entering Infinite Loop Handler')
        try:
            while True:
                time.sleep(200)

        except KeyboardInterrupt:
            GPIO.cleanup()



if __name__ == '__main__':
    try:
        keg_washer = KegWasher(pin_config, mode_config)
        keg_washer.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
    GPIO.cleanup()
