=======
History
=======

0.10.0 (TBD)
------------------

* Cloud factor was removed from solar and made its own module
* IPW Topo has been fully dperecated and removed
* Dozens config file options were renamed in favor of verbosity
* New documentation

0.9.0 (2019-12-05)
------------------

* First formal release under new branching model
* Updated Weather forecast retrieval in dockerfile
* Fixed a bug with tbreak in the wind calc
* Fixed Cloud Factor typo
* Reduced designated solar hours to limit dusk and dawn effects
* Expanded tests to HRRR input data
* Performance improvements to the gridded input data calculations

0.8.0 (2019-02-06)
------------------

* Added local gradient interpolation option for use with gridded data
* Removed ipw package to installed spatialnc dependency
* Added projection info to output files

0.7.0 (2018-11-28)
------------------

* New cloud factor method for HRRR data
* Added use of WindNinja outputs from Katana package using HRRR data
* Added unit testing as well as Travis CI and Coveralls
* Added PyKrig
* Various bug fixes

0.6.0 (2018-07-13)
------------------

* Added a new feature allowing wet bulb to be used to determine the phase of the precip.
* Added a new feature to redistribute precip due to wind.
* Added in kriging as a new distribution option all distributable variables.

0.5.0 (2018-04-18)
------------------

* Removed inicheck to make its own package.
* Added in HRRR input data for new gridded type
* Fixed various bugs associated with precip
* Modularized some functions for easiuer use scripting
* Added netcdf functionality to gen_maxus
* Added first integration test

0.4.0 (2017-11-14)
------------------

* Small improvements to our config file code including: types checking, relative paths to config, auto documentation
* Fixed bugs related to precip undercatch
* Improvements to ti station data backup
* Various adjustments for better collaboration with AWSM
* Moved to a new station database format

0.3.0 (2017-09-08)
------------------

* New feature for backing up the input data for a run in csv.
* Major update to config file, enabling checking and default adding
* Updated C file prototypes.

0.2.0 (2017-05-09)
------------------

* SMRF can run with Python 3
* Fixed indexing issue in wind
* Minor Config file improvements.