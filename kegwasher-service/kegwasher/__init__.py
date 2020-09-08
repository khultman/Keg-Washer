# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>

import logging
import os

from kegwasher.actions import *
from kegwasher.config import *
from kegwasher.hardware import *
from kegwasher.linked_list import *
from kegwasher.operations import *
from kegwasher.pca955x import *
from kegwasher.service import *


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
