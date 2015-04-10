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


def _get_toplevel_directory():
    cmd = "git rev-parse --show-toplevel"
    return subprocess.check_output(cmd.split()).rstrip()


def _get_username(repo):
    for remote in repo.remotes:
        if remote.name == "origin":
            break
    url = remote.url
    for prefix in PREFIXES:
        if url.startswith(prefix):
            return url.replace(prefix, "").split('/')[0]


def _get_remote_repo_name(repo):
    username = _get_username(repo)
    for remote in repo.remotes:
        if remote.name == "origin":
            break
    url = remote.url
    for prefix in PREFIXES:
        if url.startswith(prefix):
            rname = url.lstrip(prefix + username).rstrip(".git").lstrip('/')
            return rname


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
            body = "".join([ln.replace('#', '').lstrip() for ln in body])
        else:
            body = title
        fixmes.append(dict(title=title, body=body))
    return fixmes


def report_issue(repo, payload, username, password):
    url = URL.format(username=username, repo=_get_remote_repo_name(repo))
    password = keyring.get_password("pyticks", username)
    auth = HTTPBasicAuth(username, password)
    s = session()
    result = s.post(url, data=payload, auth=auth)
    print result


def find_files(repo):
    files = []
    for item in repo.tree().traverse():
        files.append(op.join(repo.working_dir, item.path))
    return files


def main():
    working_dir = _get_toplevel_directory()
    repo = Repo(working_dir)
    files = find_files(repo)
    for filepath in files:
        if op.isfile(filepath):
            fixmes = _find_fixme(filepath)
            if len(fixmes) > 0:
                username = _get_username(repo)
                password = keyring.get_password("pyticks", username)
                for issue in fixmes:
                    report_issue(repo, json.dumps(issue), username, password)
