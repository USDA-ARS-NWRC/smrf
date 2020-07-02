# Spatial Modeling for Resources Framework

[![GitHub version](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf.svg)](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.898158.svg)](https://doi.org/10.5281/zenodo.898158)
[![DOI](https://readthedocs.org/projects/smrf/badge/)](https://smrf.readthedocs.io)
[![Docker Build Status](https://img.shields.io/docker/build/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Docker Automated build](https://img.shields.io/docker/automated/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Build Status](https://travis-ci.org/USDA-ARS-NWRC/smrf.svg?branch=develop)](https://travis-ci.org/USDA-ARS-NWRC/smrf)
[![Coverage Status](https://coveralls.io/repos/github/USDA-ARS-NWRC/smrf/badge.svg?branch=HEAD)](https://coveralls.io/github/USDA-ARS-NWRC/smrf?branch=HEAD)

Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to increase the flexibility of taking measured weather data and distributing the point measurements across a watershed. SMRF was developed to be used as an operational or research framework, where ease of use, efficiency, and ability to run in near real time are high priorities.

Read the [full documentation for SMRF](https://smrf.readthedocs.io) including up to date installation instructions.

- [Spatial Modeling for Resources Framework](#spatial-modeling-for-resources-framework)
  - [Installation](#installation)
    - [System dependencies](#system-dependencies)
  - [Topo setup](#topo-setup)
  - [Input data](#input-data)
  - [Running SMRF](#running-smrf)
  - [Docker](#docker)

## Installation

```bash
python3 -m pip install smrf-dev
```

To install SMRF locally on Linux of MacOSX, first clone the repository and build into a virtual environment. This requires `gcc <= 9.0`. The general steps are as follows and will test the SMRF installation by running the tests.

Clone from the repository

```bash
git clone https://github.com/USDA-ARS-NWRC/smrf.git
```

And install the requirements, SMRF and run the tests.

```bash
python3 -m pip install -r requirements_dev.txt
python3 setup.py install
```

To optionally verify the installation, run the unit tests

```bash
python3 -m unittest -v
```

For Windows, the install method is using [Docker](#Docker).

### System dependencies

If using SMRF with gridded weather data from GRIB files, you will need the system dependancy for `eccodes` which is a GRIB file reader.

## Topo setup

The topo provides SMRF with the following static layers:

1. Digital elevation model
2. Vegetation type
3. Vegetation height
4. Vegetation extinction coefficient
5. Vegetation optical transmissivity
6. Basin mask (optional)

All these layers are stored in a netCDF file, typically referred to the `topo.nc` file.

While the `topo.nc` file can be generated manually, a great option is to use [basin_setup](https://github.com/USDA-ARS-NWRC/basin_setup) which creates a topo file that is compatible with SMRF and AWSM.

## Input data

Input meterological data for SMRF requires the following variables:

- Air temperature
- Vapor pressure
- Precipitation
- Wind speed and direction
- Cloud factor (percentage between 0 and 1 of incoming solar obstructed by clouds)

The data can be supplied through the following formats:

- CSV files
- [MySQL database](https://github.com/USDA-ARS-NWRC/weather_database)
- Weather Research and Forecasting (WRF) outputs
- High Resolution Rapid Refresh (HRRR)
- Generic netCDF

## Running SMRF

There are two ways to run SMRF, first is through the `run_smrf` command or through the SMRF API. If SMRF is being used as input to a snow or hydrology model, we recommend to use `run_smrf` as it will generate all the input required. See the full documentation for more details.

```bash
run_smrf <config_file>
```

## Docker

SMRF is also built into a docker image to make it easy to install on any operating system. The docker images are built automatically from the Github repository and include the latest code base or stable release images.

The SMRF docker image has a folder meant to mount data inside the docker image at `/data`.

```bash
docker run -v <path to data>:/data usdaarsnwrc/smrf run_smrf <path to config>
```

The `<path to data>` should be the path to where the configuration file, data and topo are on the host machine. This will also be the location to where the SMRF output will go.

**NOTE:** The paths in the configuration file must be adjusted for being inside the docker image. For example, in the command above the path to the config will be inside the docker image. This would be `/data/config.ini` and not the path on the host machine.

In a way that ARS uses this, we keep the config, topo and data on one location as the files are fairly small. The output then is put in another location as it file size can be much larger. To facilitate this, mount the input and output data separately and modify the configuration paths.

```bash
docker run -v <input>:/data/input -v <output>:/data/output usdaarsnwrc/smrf run_smrf <path to config>
```