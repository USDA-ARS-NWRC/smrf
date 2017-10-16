
Installation
============

SMRF relies on the Image Processing Workbench (IPW), which must be installed
first. However, IPW currently has not been tested to run natively on Windows
and must use Docker. Check the Windows section for how to run.

The authors recommend using a Python `virtual environment`_  to reduce
the possibility of a dependency issue.


.. _virtual environment: https://virtualenv.pypa.io


Install IPW
-----------

Clone IPW  using the command below and follow the instructions in the Install
text file. If you would prefer to read the file in your browser `click here`_.

.. _click here: https://github.com/USDA-ARS-NWRC/ipw/blob/master/Install

.. code:: console

  $ git clone https://github.com/USDA-ARS-NWRC/ipw.git


Ubuntu
------

1. Install system dependencies

   * gcc greater than 4.8
   * Python compiled with gcc


2. Ensure the following environment variables are set and readable by Python

   * $IPW, and $IPW/bin environment variable is set.
   * WORKDIR, the location where temporary files are created and modified which
     is not default on Linux. Use ~/tmp for example.
   * PATH, is set and readable by Python (mainly if running inside an IDE
     environment).


3. Install SMRF with following

  .. code-block:: console

    git clone https://github.com/USDA-ARS-NWRC/smrf.git
    cd smrf
    pip install -r requirements.txt
    python setup.py install


4. Test the installation with
  .. code::

    run_smrf --help


Mac OSX
-------

Mac OSX greater than 10.8 is required to run SMRF. Mac OSX comes standard with Python installed with the default
compiler clang.  To utilize multi-threading and parallel processing, gcc must be installed with Python compiled
with that gcc version.

1. MacPorts Install system dependencies

.. code-block:: bash

   port install gcc5
   port install python27

2. Or Homebrew install system dependencies

.. code-block:: python

   brew tap homebrew/versions
   brew install gcc5
   brew install python

.. note::
   Ensure that the correct gcc and Python are activated, use ``gcc --version``
   and ``python --version``. If they are not set, use Homebrew or MacPorts
   activate features.

3. Ensure the following environment variables are set and readable by Python
    * $IPW, and $IPW/bin environment variable is set
    * PATH, is set and readable by Python (mainly if running inside an IDE
      environment)

4. Install SMRF

.. code-block:: console

   git clone https://github.com/USDA-ARS-NWRC/smrf.git
   cd smrf
   pip install -r requirements.txt
   python setup.py install

 5. Test the installation with
   .. code::
     run_smrf --help


Windows
-------

Since IPW has not been tested to run in Window, Docker will have to be used
to run SMRF.  The docker image for SMRF can be found on docker hub
`here <https://hub.docker.com/r/scotthavens/smrf/>`_
