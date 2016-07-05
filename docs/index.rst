.. SMRF documentation master file, created by
   sphinx-quickstart on Sun Jul  3 08:08:09 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Spatial Modeling for Resources Framework
========================================

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

.. toctree::
   :maxdepth: 2
   
   install
   quick_start
   api
   


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

