.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/USDA-ARS-NWRC/smrf/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it. If the added feature expands the options
available in the config flie, please make them available by adding to the CoreConfig.ini
in ./smrf/framework/CoreConfig.ini. For more information on syntax for this,
please reference the configuration section.

Write Documentation
~~~~~~~~~~~~~~~~~~~

SMRF could always use more documentation, whether as part of the
official SMRF docs, in docstrings, or even on the web in blog posts,
articles, and such.

Versioning
----------
SMRF uses bumpversion to version control. More about bumpversion can be found at
https://pypi.python.org/pypi/bumpversion. This can easily be used with the
command::

  $ bumpbversion patch --tag

Don't forget to push your tags afterwards with::

  $ git push origin --tags

Currently SMRF is version 0.8.12 The development team of SMRF attempted to adhere

to semantic versioning. Here is the basics taken from the semantic versioning website.

  * Patch version Z (x.y.Z | x > 0) MUST be incremented if only backwards compatible bug fixes are introduced.
    A bug fix is defined as an internal change that fixes incorrect behavior.
  * Minor version Y (x.Y.z | x > 0) MUST be incremented if new, backwards compatible functionality is introduced to the public API.
    It MUST be incremented if any public API functionality is marked as deprecated.
    It MAY be incremented if substantial new functionality or improvements are introduced within the private code.
    It MAY include patch level changes. Patch version MUST be reset to 0 when minor version is incremented
  * Major version X (X.y.z | X > 0) MUST be incremented if any backwards incompatible changes are introduced to the public API.
    It MAY include minor and patch level changes. Patch and minor version MUST be reset to 0 when major version is incremented.

For more info on versions see http://semver.org

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/USDA-ARS-NWRC/smrf/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `smrf` for local development.

1. Fork the `smrf` repo on GitHub.
2. Clone your fork locally::

    $ git clone https://github.com/your_name_here/smrf

3. Install your local copy into a virtualenv. Assuming you have
   virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv smrf
    $ cd smrf/
    $ pip install -r requirements.txt
    $ pip install -e .

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the tests, including testing other Python versions with tox::

    $ flake8 smrf
    $ python setup.py test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.6, 2.7, 3.3, 3.4 and 3.5, and for PyPy. Check
   https://travis-ci.org/scotthavens/smrf/pull_requests
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

    $ python -m unittest discover -v

To check the coverage of the tests::

	$ coverage run --source smrf setup.py test
	$ coverage html
	$ xdg-open htmlcov/index.html
