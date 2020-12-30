#!/usr/bin/env python
# encoding: utf8
#
#   views/AnsiColors.py – part of the "deploy" build automation system
#   Copyright (C) 2020  Dennis Terhorst
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
'''
Terminal Colors module.

This module provides functions to color terminal output. If not used in an
interactive terminal colors will automatically be turned off. This allows
colored output to be redirected to files without the color escape sequences.
'''
from sys import stdout
import logging

log = logging.getLogger(__name__)


def red(text):
    'Format text.'
    return f"\033[31m{text}\033[m"


def green(text):
    'Format text.'
    return f"\033[32m{text}\033[m"


def blue(text):
    'Format text.'
    return f"\033[34m{text}\033[m"


def orange(text):
    'Format text.'
    return f"\033[00;33m{text}\033[m"


def yellow(text):
    'Format text.'
    return f"\033[00;33m{text}\033[m"


def gray(text):
    'Format text.'
    return f"\033[00;90m{text}\033[m"


def bold(text):
    'Format text.'
    return f"\033[01m{text}\033[m"


def nocolor(text):
    'Format text.'
    return text


if not stdout.isatty():
    log.info("output to a non-tty.")
    red = nocolor
    green = nocolor
    blue = nocolor
    orange = nocolor
    yellow = nocolor
    gray = nocolor
    bold = nocolor
