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

    """The main class of the pyticks module.

    Most of what this module does should be accessible through this class. It
    provides a method `run`, which does all the heavy lifting. """

    def __init__(self):
        self.working_dir = self._get_toplevel_directory()
        self.repo = Repo(self.working_dir)
        self.username = self._get_username()
        self.password = keyring.get_password("pyticks", self.username)
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.files = []
        self.find_files()

    def _get_username(self):
        """Get the GitHub username

        :return: username
        :rtype: Str
        """
        for remote in self.repo.remotes:
            if remote.name == "origin":
                break
        url = remote.url
        for prefix in PREFIXES:
            if url.startswith(prefix):
                return url.replace(prefix, "").split('/')[0]

    def _get_toplevel_directory(self):
        """Get the toplevel working directory for the current git repo.

        :rtype: Str
        """
        cmd = "git rev-parse --show-toplevel"
        return subprocess.check_output(cmd.split()).rstrip()

    def find_files(self):
        """Find all the tracked files. Equivalent to git ls-files."""
        for item in self.repo.tree().traverse():
            self.files.append(op.join(self.repo.working_dir, item.path))

    def report_issue(self, payload):
        """Post an issue to GitHub.

        :param payload: Dictionary containing payload to deliver through the
        GitHub API.
        :type payload: Dict
        :return: HTTP response
        :rtype: requests.models.Response
        """
        url = URL.format(username=self.username,
                         repo=self._get_remote_repo_name())
        s = session()
        return s.post(url, data=json.dumps(payload), auth=self.auth)

    def run(self):
        """Parse all tracked files, get FIXMEs, create issues on GitHub."""

        for filepath in self.files:
            if op.isfile(filepath):
                fixmes = self._find_fixme(filepath)
                if len(fixmes) > 0:
                    for issue in fixmes:
                        self.report_issue(issue)

    def _find_fixme(self, filepath):
        """Find all comments marked FIXME in the file at `filepath`.

        :param filepath: path to file which is to be parsed for FIXMEs
        :type filepath: Str
        :return: List of FIXME comments
        :rtype: list
        """
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
        """Get the name of the remote repository by parsing the remote url.

        :return: Name of the remote url.
        :rtype: str
        """
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
