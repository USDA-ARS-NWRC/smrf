# Spatial Modeling for Resources Framework

[![GitHub version](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf.svg)](https://badge.fury.io/gh/USDA-ARS-NWRC%2Fsmrf)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.898158.svg)](https://doi.org/10.5281/zenodo.898158)
[![DOI](https://readthedocs.org/projects/smrf/badge/)](https://smrf.readthedocs.io)


Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at
the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to
increase the flexibility of taking measured weather data and distributing
the point measurements across a watershed. SMRF was developed to be used as an
operational or research framework, where ease of use, efficiency, and ability to
run in near real time are high priorities.

#### Usage 
Read the full documentation for [SMRF](https://smrf.readthedocs.io) including up to
date installation instructions.


SMRF
-------------------------------------------------------
Spatial Modeling for Resources Framework (SMRF) was developed by Dr. Scott Havens at the USDA Agricultural Research Service (ARS) in Boise, ID. SMRF was designed to increase the flexibility of taking measured weather data and distributing the point measurements across a watershed. SMRF was developed to be used as an operational or research framework, where ease of use, efficiency, and ability to run in near real time are high priorities.

Starting
-------------------------------------------------------

To mount a data volume, so that you can share data between the local filesystem and the docker, the ``-v`` option must be used.  For a more in depth dicussion and tutorial, read https://docs.docker.com/engine/userguide/containers/dockervolumes/. The container has a shared data volume at ``/data`` where the container can access the local filesystem. 

When the image is ran, it will go into the Python terminal within the image. Within this terminal, SMRF can be imported. The command ``/bin/bash`` can be appended to the end of docker run to enter into the docker terminal for full control. It will start in the ``/data`` location with SMRF code in ``/home/smrf/smrf``.

For Linux
``docker run -v <path>:/data -it scotthavens/smrf [/bin/bash]``

For MacOSX:
``docker run -v /Users/<path>:/data -it scotthavens/smrf [/bin/bash]``

For Windows:
``docker run -v /c/Users/<path>:/data -it scotthavens/smrf [/bin/bash]``

Mac and Windows use a lightweight virtual machine environment to run docker. With
the Docker Toolbox, an Oracle Virtual Machine should become available, which will
run the docker environment.  Open Oracle Virtual Machine to change the amount of
resources that docker can use, whether it be processors or RAM.

Running the test
-------------------------------------------------------------

```
docker run -v <path>:/data -it scotthavens/smrf /bin/bash
cd /home/smrf/smrf
python run_smrf.py test_data/testConfigDocker.ini
```

The output netCDF files will be placed in the ``<path>`` location.
