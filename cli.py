#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""pyticks

Usage:
    pyticks [--force]

Options:
    -f --force      Force updating issues by searching the entire repo.

"""

from docopt import docopt
import pyticks


def main():
    arguments = docopt(__doc__, version="pyticks v0.0.1")
    if not arguments.get("--force"):
        pyticks.main()
