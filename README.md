[![Build Status](https://travis-ci.org/jaidevd/pyticks.svg?branch=master)](https://travis-ci.org/jaidevd/pyticks)
# pyticks
Turn all the FIXME and TODO comments in your code to GitHub issues.

Motivation
==========

I often write notes and comments in my source and forget about them. GitHub
issues are relatively less easy to ignore. PyTicks is a command line tool that
scans code for comments with certain prefixes and turns them into GitHub
issues. The idea is to make it robust enough to use it as a pre-push git hook.

There are a few open source projects that do something very similar to what
PyTicks does. But none of them were cutting it for me for a various reasons
like requiring Eclipse, only supporting C source code, not being smart enough
to ignore issues already created, etc.

Installation & Usage
====================

Clone the repo and install the dependencies as follows:

```bash
$ pip install -r requirements
```

Install the script itself by running:

```bash
$ python setup.py install
```

The `pyticks` script should now be available in the bin directory of your
Python prefix.

To use the script, navigate to local clone of a GitHub repository and do the
following:

```bash
$ pyticks -u github_username -p github_password
```

If you don't want to specify your username and password every time you
use PyTicks, you can add the following line to your `netrc` file.

```
machine github login github_username password github_password
```

After this, the script should be usable simply as

```
$ pyticks
```

**Note**: PyTicks looks for the netrc file in the default location, i.e.
`$HOME/.netrc`, but you can specify an arbitrary location by setting the
`PYTICKS_NETRC` environment variable to your preferred location.

The script will parse your code for any comments that are prefixed with
`# FIXME: ` (indentation does not matter, all comments are fully dedented) and
converts them into GitHub issues. Here's how it really works - assume that your
code has the following lines:

```python
def foo():
    # FIXME: foo is not implemented
    # This method raises NotImplementedError
    raise NotImplementedError
```

PyTicks infers the title of the issue from the first line containing the
prefix, and every commented line following the title makes up the body of the
issue. Thus, in this case, PyTicks will create an issue titled "foo is not
implemented" and the body of the issue will be "This method raises
NotImplementedError".

Note that empty lines are ignored. So if you want a comment to be a part of the
issue's body, make sure that there are no line breaks. Consider this example.

```python
def foo():
    # FIXME: Recursion
    # Did you mean recursion?
    
    # Yes I meant recursion.
    return foo()
```

Here, only the first two comment lines within the body of the function will go
into the issue. PyTicks stops populating the body of the issue when it sees the
first line that is not a comment.

*NOTE*: Only tested on Linux.

ToDos:
------

* Make it smarter
    - the script should only look for issues in commits that don't exist in the
    remote
    - users should be warned if an identical issue already exists (same user,
        same title)

* Make it fully configurable
    - The user should be able to specify what prefixes to use for issues, not
    just the string "FIXME" but arbitrary strings.
    - The user should be able to specify git branches in which issues are
        searched.
    - The user should be able to assign issues by using simple syntax in the
        code. Eg, by using trailing comments like `#assignee: username`. Same
        with milestones.

* Multi-language support:
    - Depending on the extensions of the file, the script should be able to
        pick up the right comment characters/strings.

