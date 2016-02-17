#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 jaidev <jaidev@newton>
#
# Distributed under terms of the MIT license.

"""Tests."""

import ast
import os
import os.path as op
import shutil
import unittest
import git
import json
import pyticks
import tempfile
from ConfigParser import RawConfigParser
import responses


class TestBase(unittest.TestCase):
    """Base class for all test cases. Sets up the metadata required for the
   tests."""

    @classmethod
    def setUpClass(cls):
        cls.testrepo_location = op.join(op.abspath(op.dirname(__file__)),
                                        "testdata", "testrepo")

        # create a sample .pyticksrc file
        cls.sample_pyticksrc_dest = op.join(cls.testrepo_location, ".pyticksrc")
        cls.parser = RawConfigParser()
        cls.parser.add_section("main")
        cls.parser.set("main", "default_remote", "upstream")
        cls.cache_location = tempfile.NamedTemporaryFile(delete=False)
        with open(cls.cache_location.name, "w") as fCache:
            json.dump({}, fCache)
        cls.parser.set("main", "cache_location", cls.cache_location.name)
        with open(cls.sample_pyticksrc_dest, "w") as fConf:
            cls.parser.write(fConf)

        # stage some files
        cls.repo = git.Repo.init(cls.testrepo_location)
        cls.repo.create_remote("origin", "https://github.com/jaidevd/testrepo.git")
        cls.repo.create_remote("upstream", "https://github.com/foobar/testrepo.git")
        cls.repo.index.add([op.join(cls.testrepo_location, "file1.py")])
        cls.repo.index.add([op.join(cls.testrepo_location, "file2.md")])
        cls.repo.index.add([op.join(cls.testrepo_location, ".pyticksrc")])
        cls.repo.index.commit("Initial commit.")

    @classmethod
    def tearDownClass(cls):
        # De-init the git repo
        shutil.rmtree(op.join(cls.testrepo_location, ".git"))
        # remove sample .pyticksrc
        os.unlink(cls.sample_pyticksrc_dest)
        # remove cache
        os.unlink(cls.cache_location.name)


class TestMisc(TestBase):
    """Miscellaneous tests for the module."""

    def test_untracked(self):
        """Test if untracked files are found properly."""
        self.assertEqual(len(self.repo.untracked_files), 1)
        self.assertIn("untracked_file.py", self.repo.untracked_files)

    def test_locate_config_file(self):
        """Test if the config file is located properly."""
        config_path = pyticks.locate_config_file(self.testrepo_location)
        self.assertEqual(config_path, self.sample_pyticksrc_dest)

    def test_locate_config_file_no_args(self):
        """Test if the config file locator when the top level directory is not
        specified."""
        self.assertIsNone(pyticks.locate_config_file())


class TestConfig(TestBase):

    def setUp(self):
        self.config = pyticks.Configuration(self.testrepo_location)

    def test_cache_location(self):
        """Test if the configuration object detects the cache location."""
        self.assertEqual(self.config.cache_location, self.cache_location.name)

    def test_default_remote(self):
        """Test if the configuration object detects the default remote."""
        self.assertEqual(self.config.default_remote, "upstream")

    def test_default_remote_no_args(self):
        """Test if the configuration returns origin as the default remote when
        none is provided."""
        # Remove the default remote option from the config.
        org_remote = self.parser.get("main", "default_remote")
        self.parser.remove_option("main", "default_remote")
        with open(self.sample_pyticksrc_dest, "w") as fConf:
            self.parser.write(fConf)
        config = pyticks.Configuration(self.testrepo_location)
        try:
            self.assertTrue(config.default_remote, "origin")
        finally:
            # Write the original config back
            self.parser.set("main", "default_remote", org_remote)
            with open(self.sample_pyticksrc_dest, "w") as fConf:
                self.parser.write(fConf)


class TestPyticks(TestBase):
    """Tests for the Pyticks class."""

    def setUp(self):
        test_netrc_path = op.join(op.abspath(op.dirname(__file__)), "testdata",
                                  "sample.netrc")
        os.environ['PYTICKS_NETRC'] = test_netrc_path
        self.maxDiff = None
        self.engine = pyticks.PyTicks(working_dir=self.testrepo_location)
        self.url = pyticks.URL.format(orgname="foobar", repo="testrepo")
        self.issue1_body = json.dumps(dict(body='This method is not implemented.',
                                           title='foo is not implemented'))
        self.issue2_body = json.dumps(dict(body='Did you mean recursion?',
                                           title='Recursion'))
        self.issue3_body = json.dumps(dict(body='this is the body of the dummy issue.',
                                           title='this is a dummy issue'))
        self.issue4_body = json.dumps(dict(body='this is the body of the second issue.',
                                           title='this is another issue'))

    def test_auth(self):
        """Test if pyticks can get the correct authentication information."""
        self.assertEqual(self.engine.username, "jaidevd")
        self.assertEqual(self.engine.password, "password")

    def test_cache(self):
        """Test the caching mechanism."""
        self.assertEqual(self.engine.cache, {})

    def test_get_orgname(self):
        """Test if the correct organization/user name is extracted from the
        remote url."""
        self.assertEqual(self.engine._get_orgname(), "foobar")

    def test_get_remote_repo_name(self):
        """Test if the correct repo name is extracted from the
        remote url."""
        self.assertEqual(self.engine._get_remote_repo_name(), "testrepo")

    def test_get_toplevel_directory(self):
        """Test if the valid top level directory """
        self.assertEqual(self.engine._get_toplevel_directory(),
                         op.abspath(op.dirname(__file__)))

    def test_source_files(self):
        """Test if the tracked source files are identified by pyticks."""
        ideal = ["file1.py"]
        ideal = [op.join(self.testrepo_location, i) for i in ideal]
        self.assertItemsEqual(ideal, self.engine.files)

    def test_find_fixme(self):
        """Test if issues are found within files."""
        # FIXME: this is a dummy issue
        # this is the body of the dummy issue.

        # FIXME: this is another issue
        # this is the body of the second issue.
        fixmes = self.engine._find_fixme(__file__)
        self.assertEqual(len(fixmes), 2)
        ideal = [json.loads(self.issue3_body), json.loads(self.issue4_body)]
        for i in range(2):
            issue = ideal[i]
            self.assertEqual(issue["title"], fixmes[i]["title"])
            self.assertEqual(issue["body"], fixmes[i]["body"])

    @responses.activate
    def test_encache(self):
        """Test if issues are cached after being reported."""
        responses.add(responses.POST, self.url, status=201,
                      body=self.issue1_body, content_type="application/json")
        responses.add(responses.POST, self.url, status=201,
                      body=self.issue2_body, content_type="application/json")
        self.engine.run()
        cache = self.engine._get_cache()
        try:
            self.assertIn("testrepo", cache)
            issues = cache['testrepo']
            issues = [json.dumps(i) for i in issues]
            self.assertIn(self.issue1_body, issues)
            self.assertIn(self.issue2_body, issues)
        finally:
            self.engine.clear_cache()

    @responses.activate
    def test_report_issue(self):
        """Test if issues are reported."""
        responses.add(responses.POST, self.url, status=201,
                      body=self.issue1_body, content_type="application/json")
        responses.add(responses.POST, self.url, status=201,
                      body=self.issue2_body, content_type="application/json")
        resps = self.engine.run()
        self.assertEqual(len(resps), 2)
        self.assertEqual(responses.calls[0].request.url, self.url)
        self.assertEqual(responses.calls[1].request.url, self.url)
        self.assertEqual(ast.literal_eval(resps[0].text),
                         ast.literal_eval(self.issue1_body))


if __name__ == "__main__":
    unittest.main()
