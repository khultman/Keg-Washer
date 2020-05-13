# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import RPi.GPIO as GPIO

# Mode Configuration
# Available Mode Operations
# air_fill_closed   - Fill keg with air, all other valves closed
# air_fill_open     - Fill keg with air, waste_out valve on
# clean_closed      - Closed loop clean: cleaner_in, cleaner_rtn & pump valves on, pump on
# clean_open        - Open loop clean: cleaner_in, waste_out & pump valves on, pump on
# co2_fill_closed   - Fill keg with CO2, all other valves closed
# co2_fill_open     - Fill keg with CO2, waste_out valve on
# drain             - waste_out valve on, all other valves closed
# rinse             - water_in, waste_out & pump valves on, pump on
# sanitize          - sanitizer_in, waste_out & pump valves on, pump on
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
    },
    'sanitizer_fill': {
        'display_name': 'Fill Sanitizer',
        'operations': [
            #  Operation         Time to Run Operation
            ('santizer_fill',    10)
        ]
    },
    'cleaner_fill': {
        'display_name': 'Fill Cleaner',
        'operations': [
            #  Operation         Time to Run Operation
            ('cleaner_fill',     10)
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
    'heaters': [
        {'name': 'heater_1',     'pin': 11}
    ],
    'pumps': [
        {'name': 'pump_1',       'pin': 27}
    ],
    'switches': [
        {'name': 'mode',         'pin': 5,    'PUD': GPIO.PUD_DOWN,   'event': GPIO.BOTH,      'callback': 'sw_mode'},
        {'name': 'enter',        'pin': 6,    'PUD': GPIO.PUD_DOWN,   'event': GPIO.BOTH,      'callback': 'sw_enter'},
        {'name': 'sw_3',         'pin': 12,   'PUD': GPIO.PUD_DOWN,   'event': GPIO.BOTH,      'callback': 'sw_nc'},
        {'name': 'sw_4',         'pin': 13,   'PUD': GPIO.PUD_DOWN,   'event': GPIO.BOTH,      'callback': 'sw_nc'},
        {'name': 'abort',        'pin': 20,   'PUD': GPIO.PUD_DOWN,   'event': GPIO.RISING,    'callback': 'sw_abort'}
    ],
    'valves': [
        {'name': 'cleaner_in',   'pin': 21},
        {'name': 'sanitizer_in', 'pin': 26},
        {'name': 'water_in',     'pin': 4},
        {'name': 'pump_in',      'pin': 17},
        {'name': 'co2_in',       'pin': 18},
        {'name': 'air_in',       'pin': 22},
        {'name': 'cleaner_rtn',  'pin': 23},
        {'name': 'pump_out',     'pin': 24},
        {'name': 'waste_out',    'pin': 25}
    ]
}

