
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

SMRF was developed as a modular framework to enable new modules to be easily integrated
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
   :titlesonly:

   getting_started/index
   user_guide/index
   api/index
   zreferences


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
