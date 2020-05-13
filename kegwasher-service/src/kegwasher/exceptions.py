# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Kyle Hultman <khultman@gmail.com>


class KegwasherException(Exception):
    """
    Base Exception Class
    """


class ConfigException(KegwasherException):
    def __init__(self, message):
        super(ConfigException, self).__init__(message)
