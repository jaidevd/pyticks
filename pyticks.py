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
import subprocess
import os.path as op

from git import Repo
import keyring
from requests import session
from requests.auth import HTTPBasicAuth


URL = "https://api.github.com/repos/{username}/{repo}/issues"
PREFIXES = ["git@github.com:", "https://github.com/",
            "https://www.github.com/"]


class PyTicks(object):

    def __init__(self):
        self.working_dir = self._get_toplevel_directory()
        self.repo = Repo(self.working_dir)
        self.username = self._get_username()
        self.password = keyring.get_password("pyticks", self.username)
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.files = []
        self.find_files()

    def _get_username(self):
        for remote in self.repo.remotes:
            if remote.name == "origin":
                break
        url = remote.url
        for prefix in PREFIXES:
            if url.startswith(prefix):
                return url.replace(prefix, "").split('/')[0]

    def _get_toplevel_directory(self):
        cmd = "git rev-parse --show-toplevel"
        return subprocess.check_output(cmd.split()).rstrip()

    def find_files(self):
        for item in self.repo.tree().traverse():
            self.files.append(op.join(self.repo.working_dir, item.path))

    def report_issue(self, payload):
        url = URL.format(username=self.username,
                         repo=self._get_remote_repo_name())
        s = session()
        return s.post(url, data=json.dumps(payload), auth=self.auth)

    def run(self):
        for filepath in self.files:
            if op.isfile(filepath):
                fixmes = self._find_fixme(filepath)
                if len(fixmes) > 0:
                    for issue in fixmes:
                        self.report_issue(issue)

    def _find_fixme(self, filepath):
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
                body = "".join([ln.replace('#', '').lstrip() for ln in body])
            else:
                body = title
            fixmes.append(dict(title=title, body=body))
        return fixmes

    def _get_remote_repo_name(self):
        for remote in self.repo.remotes:
            if remote.name == "origin":
                break
        url = remote.url
        for prefix in PREFIXES:
            if url.startswith(prefix):
                rname = url.lstrip(prefix + self.username).rstrip(
                                                            ".git").lstrip('/')
                return rname


def main():
    engine = PyTicks()
    engine.run()


if __name__ == '__main__':
    main()
