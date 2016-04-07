#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Cube26 product code
#
# (C) Copyright 2015 Cube26 Software Pvt Ltd
# All right reserved.
#
# This file is confidential and NOT open source.  Do not distribute.
#

"""pyticks

Usage:
    pyticks [--username=<USERNAME>] [--password=<PASSWORD>] [--force]

Options:
    --force                    Force parse all tracked files for issues.
    -u --username=<USERNAME>   GitHub username
    -p --password=<PASSWORD>   GitHub password

"""

from docopt import docopt
from pyticks import worker


def main():
    arguments = docopt(__doc__, version="pyticks v0.0.1")
    username = arguments.get("--username")
    password = arguments.get("--password")
    worker((username, password))
