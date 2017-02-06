# Spatial Modeling for Resources Framework V 0.1.1

Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at
the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to
increase the flexibility of taking measured weather data and distributing
the point measurements across a watershed. SMRF was developed to be used as an
operational or research framework, where ease of use, efficiency, and ability to
run in near real time are high priorities.

Read the documentation full for [SMRF](https://smrf.readthedocs.io).

### Navigation
1. [Features](#features)
1. [Installation](#installation)
    1. [Ubuntu](#ubuntu)
    1. [Mac OSX](#macosz)
    1. [Windows](#windows)
1. [Quick Start](#quick_start)
1. [Credits](#credits)

## Features
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


## Installation

SMRF relies on the Image Processing Workbench (IPW), which must be installed first. However, IPW currently has not been tested to run natively on Windows and must use Docker. Check the Windows section for how to run.


### Install IPW
Clone IPW [here](https://gitlab.com/ars-snow/ipw) and follow the instructions. Note that setting the WORKDIR environment variable and is replaced by setting the tmp_dir in the configuration file.

### Ubuntu

1. Install system dependencies
    * gcc greater than 4.8
    * Python compiled with gcc

1. Ensure the following environment variables are set and readable by Python
    * $IPW, and $IPW/bin environment variable is set
    * WORKDIR, the location where temporary files are kept and used which is not default on Linux.  Use /tmp for example
    * PATH, is set and readable by Python (mainly if running inside an IDE environment)

1. Install SMRF
```
git clone https://gitlab.com/ars-snow/smrf
cd smrf
pip install -r requirements.txt
python setup.py install
```

1. Test installation ``` python run_smrf.py ```, which should output logging information to screen if ```test_data/topo/maxus.nc``` exits

### Mac OSX

Mac OSX greater than 10.8 is required to run SMRF. Mac OSX comes standard with Python installed with the default compiler clang.  To utilize multi-threading and parallel processing, gcc must be installed with Python compiled with that gcc version.

1. __MacPorts__ Install system dependencies
```
port install gcc5
port install python27
```

1.  Or __Homebrew__ install system dependencies
```
brew tap homebrew/versions
brew install gcc5
brew install python
```

1. Ensure the following environment variables are set and readable by Python
    * $IPW, and $IPW/bin environment variable is set
    * PATH, is set and readable by Python (mainly if running inside an IDE environment)

1. Install SMRF
    ```
    git clone https://gitlab.com/ars-snow/smrf
    cd smrf
    pip install -r requirements.txt
    python setup.py install
    ```

1. Test installation ``` python run_smrf.py ```, which should output logging information to screen if ```test_data/topo/maxus.nc``` exits

## Windows

Since IPW has not be tested to run in Window, Docker will have to be used to run SMRF.  The docker image can for SMRF can be found on docker hub [here](https://hub.docker.com/r/scotthavens/smrf/)


## Quick start

Check out the full documentation at at (coming soon).

To run the test dataset to ensure that SMRF is working:
```
python run_smrf.py
```


To run SMRF and generate all forcing variables for iSnobal, the general outline is as follows:
1. Gather DEM, vegitation height, vegitation transmissivity, and vegitation extinction as IPW images
1. Create the wind maxus NetCDF file using ```smrf.utils.wind_model```
1.  Change the configuration file to reflect station names, date range, and variables configurations
1. ``` python run_smrf.py your_config_file.ini```

## Credits

Checkout the following for using and distributing a package:
http://python-packaging.readthedocs.org/en/latest/minimal.html

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and 
the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.

