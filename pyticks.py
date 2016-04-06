#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

'''
PyTicks: automatically turn TODOs and FIXMEs into GitHub issues.
'''

import json
import six
import subprocess
import os.path as op
from git import Repo
from requests import session
from requests.auth import HTTPBasicAuth
if six.PY2:
    from ConfigParser import RawConfigParser, NoOptionError, NoSectionError
else:
    from configparser import RawConfigParser, NoOptionError, NoSectionError


URL = 'https://api.github.com/repos/{orgname}/{repo}/issues'
PREFIXES = ['git@github.com:', 'https://github.com/', 'git://github.com/',
            'https://www.github.com/']


def locate_config_file(tld=None):
    """Locate the config file used by pyticks."""
    if tld is None:
        tld = PyTicks._get_toplevel_directory()
    if op.exists(op.join(tld, ".pyticksrc")):
        return op.abspath(op.join(tld, ".pyticksrc"))


class Configuration(object):
    """Configuration class containing miscellaneous info used by Pyticks."""

    def __init__(self, working_dir):
        self.working_dir = working_dir
        config_fpath = locate_config_file(self.working_dir)
        self.parser = RawConfigParser()
        if config_fpath is not None:
            self.parser.read(config_fpath)

    @property
    def cache_location(self):
        """Get the path to the cache file used by Pyticks to store issues."""
        try:
            cpath = self.parser.get("main", "cache_location")
        except NoSectionError:
            return
        if not op.exists(cpath):
            open(cpath, "w").close()
        return cpath

    @property
    def default_remote(self):
        """Get the default remote out of all the remotes listed in git.
        It is on this remote that pyticks will attempt to create issues."""
        try:
            remote = self.parser.get("main", "default_remote")
            return remote
        except (NoOptionError, NoSectionError):
            return "origin"


class PyTicks(object):

    '''The main class of the pyticks module.

    Most of what this module does should be accessible through this class. It
    provides a method `run`, which does all the heavy lifting. '''

    def __init__(self, auth=None, working_dir=None):
        if working_dir is None:
            self.working_dir = self._get_toplevel_directory()
        else:
            self.working_dir = working_dir
        self.repo = Repo(self.working_dir)
        if (auth is not None) and (None not in auth):
            self.username, self.password = auth
        else:
            self.username, self.password = self.get_netrc_auth()
        self.auth = HTTPBasicAuth(self.username, self.password)
        self.config = Configuration(self.working_dir)
        self.cache = self._get_cache()

    def _get_cache(self):
        """Get the cache as a dictionary."""
        if self.config.cache_location is not None:
            with open(self.config.cache_location, "r") as fin:
                cache = json.load(fin)
            return cache
        return {}

    def encache(self, payload):
        """Add the payload of the current issue request to the cache."""
        issues = self.cache.get(self._get_remote_repo_name(), [])
        if len(issues) == 0:
            self.cache[self._get_remote_repo_name()] = [payload]
        else:
            issues.append(payload)
        with open(self.config.cache_location, "w") as fout:
            json.dump(self.cache, fout)

    def clear_cache(self):
        with open(self.config.cache_location, "w") as fin:
            json.dump({}, fin)

    def get_netrc_auth(self):
        """Get the authentication credentials from the netrc file."""
        import os
        import netrc
        if os.environ.get("PYTICKS_NETRC", False):
            netrc_path = os.environ['PYTICKS_NETRC']
        else:
            netrc_path = op.join(op.expanduser("~"), ".netrc")
        creds = netrc.netrc(netrc_path)
        username, _, password = creds.authenticators('github')
        return username, password

    def _get_orgname(self):
        """Get the name of the GitHub organization or the user who owns the
        repo on which the issue is to be created."""
        for remote in self.repo.remotes:
            if remote.name == self.config.default_remote:
                break
        url = remote.url
        for prefix in PREFIXES:
            if url.startswith(prefix):
                return url.replace(prefix, "").split(r'/')[0]

    @staticmethod
    def _get_toplevel_directory():
        '''Get the toplevel working directory for the current git repo.

        :rtype: Str
        '''
        cmd = 'git rev-parse --show-toplevel'
        return subprocess.check_output(cmd.split()).rstrip().decode('utf-8')

    @property
    def files(self):
        '''Find all the *.py tracked files. Equivalent to git ls-files.'''
        files = self.repo.git.ls_files().splitlines()
        return [op.join(self.repo.working_dir, f) for f in files if f.endswith(".py")]

    def report_issue(self, payload):
        '''Post an issue to GitHub.

        :param payload: Dictionary containing payload to deliver through the
        GitHub API.
        :type payload: Dict
        :return: HTTP response
        :rtype: requests.models.Response
        '''
        if payload not in self.cache.get(self._get_remote_repo_name(), []):
            url = URL.format(orgname=self._get_orgname(),
                            repo=self._get_remote_repo_name())
            s = session()
            response = s.post(url, data=json.dumps(payload), auth=self.auth)
            if response.status_code == 201:
                self.encache(payload)
            return response
        else:
            print("Issue already filed. Skipping.")

    def run(self):
        '''Parse all tracked files, get FIXMEs, create issues on GitHub.'''
        responses = []
        for filepath in self.files:
            if op.isfile(filepath):
                fixmes = self._find_fixme(filepath)
                if len(fixmes) > 0:
                    for issue in fixmes:
                        responses.append(self.report_issue(issue))
        return responses

    @staticmethod
    def _find_fixme(filepath):
        '''Find all comments marked FIXME in the file at `filepath`.

        :param filepath: path to file which is to be parsed for FIXMEs
        :type filepath: Str
        :return: List of FIXME comments
        :rtype: list
        '''
        with open(filepath, 'r') as f:
            lines = [line.rstrip() for line in f.readlines()]
        anchors = []
        for i in range(len(lines)):
            line = lines[i]
            if line.lstrip().startswith('# FIXME: '):
                anchors.append(i)
        fixmes = []
        for anchor in anchors:
            title = lines[anchor].replace('# FIXME: ', '').lstrip()
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
                body = ''.join([ln.replace('#', '').lstrip() for ln in body])
            else:
                body = title
            fixmes.append(dict(title=title, body=body))
        return fixmes

    def _get_remote_repo_name(self):
        '''Get the name of the remote repository by parsing the remote url.

        :return: Name of the remote url.
        :rtype: str
        '''
        for remote in self.repo.remotes:
            if remote.name == self.config.default_remote:
                break
        url = remote.url
        for prefix in PREFIXES:
            if url.startswith(prefix):
                rname = url.replace(prefix + self._get_orgname() + '/',
                                    '').rstrip('.git').lstrip('/')
                return rname


def main(auth):
    engine = PyTicks(auth)
    print(engine.run())


if __name__ == '__main__':
    main()
