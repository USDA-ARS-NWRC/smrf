===============================
Spatial Modeling for Resources Framework
===============================

Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at 
the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to
increase the flexibility of taking measured weather data and distributing
the point measurements across a watershed. SMRF was developed to be used as an
operational or research framework, where ease of use, efficiency, and ability to 
run in near real time are high priorities.

Features
--------

SMRF was developed as a modular framework to enable new modules to be easily intigrated
and utilized.

* Load data into SMRF from MySQL database, CSV files, or gridded climate models (i.e. WRF)
* Variables currently implemented:
    * Air temperature
    * Vapor pressure
    * Precipitation mass, phase, density, and percent snow
    * Wind speed and direction
    * Solar radiation
    * Thermal radiation
* Output variables to NetCDF files
* Data queue for multithreaded application
* Computation tasks implemented in C


Install
--------

1. Ensure the following environment variables are set and readable by Python:
    * IPW, and $IPW/bin environment variable is set
    * TMPDIR, the location of the system's temporary files
    * PATH, is set and readable by Python (mainly if running inside an IDE environment)

2. Install
    * python setup.py clean
    * python setup.py build_ext --inplace, this will compile modules in place for using the test_data
    * python setup.py build
    * (sudo) python setup.py install


Credits
---------

Checkout the following for using and distributing a package:
http://python-packaging.readthedocs.org/en/latest/minimal.html

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
