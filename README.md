# Spatial Modeling for Resources Framework

[![GitHub version](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf.svg)](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.898158.svg)](https://doi.org/10.5281/zenodo.898158)
[![DOI](https://readthedocs.org/projects/smrf/badge/)](https://smrf.readthedocs.io)
[![Docker Build Status](https://img.shields.io/docker/build/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Docker Automated build](https://img.shields.io/docker/automated/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Build Status](https://travis-ci.org/USDA-ARS-NWRC/smrf.svg?branch=develop)](https://travis-ci.org/USDA-ARS-NWRC/smrf)
[![Coverage Status](https://coveralls.io/repos/github/USDA-ARS-NWRC/smrf/badge.svg?branch=HEAD)](https://coveralls.io/github/USDA-ARS-NWRC/smrf?branch=HEAD)

Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to increase the flexibility of taking measured weather data and distributing the point measurements across a watershed. SMRF was developed to be used as an operational or research framework, where ease of use, efficiency, and ability to run in near real time are high priorities.

Read the full documentation for [SMRF](https://smrf.readthedocs.io) including up to date installation instructions.

## Installation

To install SMRF locally on Linux of MacOSX, first clone the repository and build into a virtual environment. This requires `gcc <= 9.0`. The general steps are as follows and will test the SMRF installation by running the tests.

Clone from the repository

```bash
git clone https://github.com/USDA-ARS-NWRC/smrf.git
```

And install the requirements, SMRF and run the tests.

```bash
python3 -m pip install -r requirements_dev.txt
python3 setup.py install
python3 -m unittest -v
```

For Windows, the install method is using [Docker](#Docker).



## Docker

To mount a data volume, so that you can share data between the local file
system and the docker, the `-v` option must be used. For a more in depth
discussion and tutorial, read
https://docs.docker.com/engine/userguide/containers/dockervolumes/. The
container has a shared data volume at `/data` where the container can access
the local file system.

When the image is ran, it will go into the Python terminal within the image.
Within this terminal, SMRF can be imported. The command `/bin/bash` can be
appended to the end of docker run to enter into the docker terminal for full
control. It will start in the `/data` location with SMRF code in `/code/smrf`.

For Linux
`docker run -v <path>:/data -it usdaarsnwrc/smrf [/bin/bash]`

For MacOSX:
`docker run -v /Users/<path>:/data -it usdaarsnwrc/smrf [/bin/bash]`

For Windows:
`docker run -v /c/Users/<path>:/data -it usdaarsnwrc/smrf [/bin/bash]`
