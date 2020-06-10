===============
Getting started
===============

Installation
------------

To install SMRF locally on Linux of MacOSX, first clone the repository and build into a
virtual environment. The general steps are as follows and will
test the SMRF installation by running the tests.

Clone from the repository

.. code:: bash

    git clone https://github.com/USDA-ARS-NWRC/smrf.git


And install the requirements, SMRF and run the tests.

.. code:: bash

    python3 -m pip install -r requirements_dev.txt
    python3 setup.py install
    python3 -m unittest -v


For in-depth instructions and specific requirements for SMRF, check out the the :doc:`installation page <install>` 

For Windows, the install method is using Docker.

.. toctree::
    :maxdepth: 2

    install
    create_topo
    create_config
    run_smrf
    docker
    CONTRIBUTING
    HISTORY