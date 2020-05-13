# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>


class KegwasherException(Exception):
    """
    Base Exception Class
    """


class ConfigError(KegwasherException):
    def __init__(self, message):
        super(ConfigError, self).__init__(message)
