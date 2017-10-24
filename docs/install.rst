
Installation
============

SMRF relies on the Image Processing Workbench (IPW) so it must be installed first.
IPW currently has not been tested to run natively on Windows and must use
Docker. Check the `Windows`_ section for how to run. Please go through and
install the dependencies for your system prior to install install IPW and SMRF.


Ubuntu
------

SMRF is actively developed on Ubuntu 16.04 LTS and has been tested on 14.04 as
well. The system requirements are:

 * gcc greater than 4.8
 * Python compiled with gcc


Mac OSX
-------

Mac OSX greater than 10.8 is required to run SMRF. Mac OSX comes standard with
Python installed with the default compiler clang. To utilize multi-threading
and parallel processing, gcc must be installed with Python compiled with that
gcc version.

Install the system dependencies using MacPorts or homebrew:

  a. MacPorts install system dependencies

    .. code-block:: bash

       port install gcc5
       port install python27

  b.  Homebrew install system dependencies

    .. code-block:: python

       brew tap homebrew/versions
       brew install gcc5
       brew install python

.. note::
   Ensure that the correct gcc and Python are activated, use ``gcc --version``
   and ``python --version``. If they are not set, use Homebrew or MacPorts
   activate features.

Windows
-------

Since IPW has not been tested to run in Window, Docker will have to be used
to run SMRF.  The docker image for SMRF can be found on docker hub
`here <https://hub.docker.com/r/scotthavens/smrf/>`_. The docker image is
already setup to run smrf so the following steps do not apply for running out
of a docker.


Installing IPW
--------------

Clone IPW  using the command below and follow the instructions in the Install
text file. If you would prefer to read the file in your browser `click here`_.

.. _click here: https://github.com/USDA-ARS-NWRC/ipw/blob/master/Install

.. code:: console

    git clone https://github.com/USDA-ARS-NWRC/ipw.git

Double check that the following environment variables are set and readable by Python

   * $IPW, and $IPW/bin environment variable is set.
   * WORKDIR, the location where temporary files are created and modified which
     is not default on Linux. Use ~/tmp for example.
   * PATH, is set and readable by Python (mainly if running inside an IDE
     environment).


Installing SMRF
---------------

Once the dependencies have been installed for your respective system, the
following will install smrf. It is preferable to use a Python
   `virtual environment`_  to reduce the possibility of a dependency issue.

.. _virtual environment: https://virtualenv.pypa.io

1. Create a virtualenv and activate it.

  .. code-block:: console

    virtualenv smrfenv
    source smrfenv/bin/activate

**Tip:** The developers recommend using an alias to quickly turn on
and off your virtual environment.


2. Clone SMRF source code from the ARS-NWRC github.

  .. code-block:: console

    git clone https://github.com/USDA-ARS-NWRC/smrf.git

3. Change directories into the SMRF directory. Install the python requirements.
   After the requirements are done, install SMRF.

  .. code-block:: console

    cd smrf
    pip install -r requirements.txt
    python setup.py install

4. (Optional) Generate a local copy of the documentation.

  .. code-block:: console

    cd docs
    make html

  To view the documentation use the preferred browser to open up the files.
  This can be done from the browser by opening the index.rst file directly or
  by the commandline like the following:

  .. code-block:: console

    google-chrome _build/html/index.html

5. Test the installation by running a small example

  .. code::

    run_smrf test_data/testConfig.ini
