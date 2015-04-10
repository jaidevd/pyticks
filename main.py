#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""
PyTicks: automatically turn TODOs and FIXMEs into GitHub issues.
"""

import json
import os.path as op

from git import Repo
from requests import session
from requests.auth import HTTPBasicAuth


auth = HTTPBasicAuth("username", "password")
URL = "https://api.github.com/repos/username/repo/issues"
ROOT = op.join(op.abspath(op.dirname(__file__)), "..", "..")


def _find_fixme(filepath):
    with open(filepath, "r") as f:
        lines = [line.rstrip() for line in f.readlines()]
    anchors = []
    for i in xrange(len(lines)):
        line = lines[i]
        if line.lstrip().startswith("# FIXME: "):
            anchors.append(i)
    fixmes = []
    for anchor in anchors:
        title = lines[anchor].replace("# FIXME: ", "")
        ix = anchor
        body = []
        while True:
            ix += 1
            try:
                if not lines[ix].lstrip().startswith('#'):
                    break
                else:
                    body.append(lines[ix].lstrip())
            except IndexError:  # end of file
                break
        if len(body) > 0:
            body = "".join(body)
        else:
            body = title
        fixmes.append(dict(title=title, body=body))
    return fixmes


def report_issue(payload):
    s = session()
    return s.post(URL, data=payload, auth=auth)


def find_files():
    repo = Repo(ROOT)
    files = []
    for item in repo.tree().traverse():
        files.append(op.join(ROOT, item.path))
    return files


if __name__ == '__main__':
    files = find_files()
    for filepath in files:
        if op.isfile(filepath):
            fixmes = _find_fixme(filepath)
            if len(fixmes) > 0:
                for issue in fixmes:
                    report_issue(json.dumps(issue))
