
Installation
============

SMRF relies on the Image Processing Workbench (IPW) so it must be installed first.
IPW currently has not been tested to run natively on Windows and must use
Docker. Check the `Windows`_ section for how to run. Please go through and
install the dependencies for your system prior to installing IPW and SMRF.

.. note::
    SMRF is only maintained for Python 3 and using Python 2 may not work.

.. note::
    SMRF uses the OpenMP specification v4.X and will not work with GCC >= 9.0.


Ubuntu
------

SMRF is actively developed on Ubuntu and requires gcc greater than 4.8 and less than 9.0.
Install the dependencies by updating, install build-essentials and installing python3-dev:

  .. code:: bash

    sudo apt-get update
    sudo apt-get install build-essential
    sudo apt-get install python3-dev


Mac OSX
-------

Mac OSX greater than 10.8 is required to run SMRF. Mac OSX comes standard with
Python installed with the default compiler clang. To utilize multi-threading
and parallel processing, gcc must be installed with Python compiled with that
gcc version.

Install the system dependencies using MacPorts or homebrew:

  a. MacPorts install system dependencies

    .. code:: bash

       port install gcc5
       port install python3

  b.  Homebrew install system dependencies

    .. code:: bash

       brew tap homebrew/versions
       brew install gcc5
       brew install python3

.. note::
   Ensure that the correct gcc and Python are activated, use ``gcc --version``
   and ``python3 --version``. If they are not set, use Homebrew or MacPorts
   activate features.

Windows
-------

Since IPW has not been tested to run in Window, Docker will have to be used
to run SMRF.  The docker image for SMRF can be found on docker hub
`here <https://hub.docker.com/r/usdaarsnwrc/smrf/>`_. The docker image is
already setup to run SMRF so the following steps do not apply for running out
of a docker.


Installing SMRF
---------------

Once the dependencies have been installed for your respective system, the
following will install smrf. It is preferable to use a Python
`virtual environment`_  to reduce the possibility of a dependency issue.

.. _virtual environment: https://virtualenv.pypa.io

1. Create a virtualenv and activate it.

  .. code:: bash

    python3 -m virtualenv .venv
    source .venv/bin/activate


2. Clone SMRF source code from the ARS-NWRC github.

  .. code:: bash

    git clone https://github.com/USDA-ARS-NWRC/smrf.git

3. Change directories into the SMRF directory. Install the python requirements.
   After the requirements are done, install SMRF.

  .. code:: bash

    cd smrf
    python3 -m pip install -r requirements_dev.txt
    python3 setup.py install

4. (Optional) Generate a local copy of the documentation.

  .. code:: bash

    make docs

  To view the documentation use the preferred browser to open up the files.
  This can be done from the browser by opening the index.rst file directly or
  by the commandline like the following:

  .. code:: bash

    google-chrome _build/html/index.html

5. Test the installation by running the test suite.

   .. code:: bash

      python3 -m unittest -v

If all tests passed, SMRF is installed. See examples for
specific types of runs. Happy SMRF-ing!
