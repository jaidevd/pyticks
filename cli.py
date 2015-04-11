#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""pyticks

Usage:
    pyticks [--username=<USERNAME>] [--password=<PASSWORD>] [--force]

Options:
    --force                    Force parse all tracked files for issues.
    -u --username=<USERNAME>   GitHub username
    -p --password=<PASSWORD>   GitHub password

"""

from docopt import docopt
import pyticks


def main():
    arguments = docopt(__doc__, version="pyticks v0.0.1")
    username = arguments.get("--username")
    password = arguments.get("--password")
    if username and password:
        pyticks.main(username, password)
