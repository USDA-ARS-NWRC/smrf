# Spatial Modeling for Resources Framework

[![GitHub version](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf.svg)](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.898158.svg)](https://doi.org/10.5281/zenodo.898158)
[![DOI](https://readthedocs.org/projects/smrf/badge/)](https://smrf.readthedocs.io)
[![Docker Build Status](https://img.shields.io/docker/build/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Docker Automated build](https://img.shields.io/docker/automated/usdaarsnwrc/smrf.svg)](https://hub.docker.com/r/usdaarsnwrc/smrf/)
[![Build Status](https://travis-ci.org/USDA-ARS-NWRC/smrf.svg?branch=develop)](https://travis-ci.org/USDA-ARS-NWRC/smrf)
[![Coverage Status](https://coveralls.io/repos/github/USDA-ARS-NWRC/smrf/badge.svg?branch=HEAD)](https://coveralls.io/github/USDA-ARS-NWRC/smrf?branch=HEAD)

Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott
Havens at the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was
designed to increase the flexibility of taking measured weather data and
distributing the point measurements across a watershed. SMRF was developed to be
used as an operational or research framework, where ease of use, efficiency,
and ability to run in near real time are high priorities.

## Usage
Read the full documentation for [SMRF](https://smrf.readthedocs.io) including
up to date installation instructions.


## Quick Start

### Native install

### Docker

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


#### Running the test

```
docker run -it usdaarsnwrc/smrf /bin/bash
cd /code/smrf
gen_maxus --out_maxus test_data/topo/maxus.nc test_data/topo/dem.ipw
run_smrf.py test_data/testConfig.ini
```

The output netCDF files will be placed in the `/code/smrf/test_data/output`
location.
