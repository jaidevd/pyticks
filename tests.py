#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""Tests."""


import json
import os
import os.path as op
import unittest
import responses
import pyticks
import subprocess
import ast
from git import Repo
import tempfile
import shutil


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tld = tempfile.mkdtemp()
        cls.repo = Repo.init(cls.tld)
        open(op.join(cls.tld, ".pyticksrc"), "w").close()

    def test_get_config_file(self):
        ideal = op.join(self.tld, ".pyticksrc")
        actual = pyticks.locate_config_file(self.tld)
        self.assertEqual(ideal, actual)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tld)


class TestPyTicks(unittest.TestCase):

    def setUp(self):
        test_netrc_path = op.join(op.abspath(op.dirname(__file__)), "testdata",
                                  "sample.netrc")
        os.environ['PYTICKS_NETRC'] = test_netrc_path
        self.maxDiff = None
        self.engine = pyticks.PyTicks()
        self.url = pyticks.URL.format(username="jaidevd", repo="pyticks")
        self.issue1_body = json.dumps(dict(
                      body='this is the body of the dummy issue.',
                      title='this is a dummy issue'))
        self.issue2_body = json.dumps(dict(
                      body='this is the body of the second issue.',
                      title='this is another issue'))

    def tearDown(self):
        del os.environ['PYTICKS_NETRC']

    def test_get_toplevel_dir(self):
        """Check if the toplevel directory is detected correctly."""
        ideal = op.abspath(op.dirname(__file__))
        self.assertEqual(self.engine.working_dir, ideal)

    def test_find_files(self):
        ideal = subprocess.check_output("git ls-files".split(),
                                        cwd=op.abspath(op.dirname(__file__)))
        ideal = ideal.splitlines()
        ideal = [op.join(op.abspath(op.dirname(__file__)), f) for f in ideal]
        ideal = [f for f in ideal if f.endswith(".py")]
        self.assertItemsEqual(ideal, self.engine.files)

    def test_find_fixme(self):
        # FIXME: this is a dummy issue
        # this is the body of the dummy issue.

        # FIXME: this is another issue
        # this is the body of the second issue.
        fixmes = self.engine._find_fixme(__file__)
        self.assertEqual(len(fixmes), 2)
        ideal = [json.loads(self.issue1_body), json.loads(self.issue2_body)]
        for i in range(2):
            issue = ideal[i]
            self.assertEqual(issue["title"], fixmes[i]["title"])
            self.assertEqual(issue["body"], fixmes[i]["body"])

    def test_auth(self):
        """Test if correct credentials are found in netrc."""
        username, password = self.engine.get_netrc_auth()
        self.assertEqual(username, "jaidevd")
        self.assertEqual(password, "password")

    @responses.activate
    def test_report_issue(self):
        responses.add(responses.POST, self.url, status=201,
                      body=self.issue1_body, content_type="application/json")
        resps = self.engine.run()
        self.assertEqual(len(resps), 2)
        self.assertEqual(responses.calls[0].request.url, self.url)
        self.assertEqual(responses.calls[1].request.url, self.url)
        self.assertEqual(ast.literal_eval(resps[0].text),
                         ast.literal_eval(self.issue1_body))

if __name__ == "__main__":
    unittest.main()
