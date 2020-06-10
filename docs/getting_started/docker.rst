SMRF and Docker
===============

SMRF is also built into a docker image to make it easy to install on any operating system.
The docker images are built automatically from the Github repository and include the latest
code base or stable release images.

The SMRF docker image has a folder meant to mount data inside the docker image at ``/data``.

.. code:: console

    docker run -v <path to data>:/data usdaarsnwrc/smrf run_smrf <path to config>

The ``<path to data>`` should be the path to where the configuration file, data and topo are on
the host machine. This will also be the location to where the SMRF output will go.

.. note::

    The paths in the configuration file must be adjusted for being inside the docker image. For example,
    in the command above the path to the config will be inside the docker image. This would be
    ``/data/config.ini`` and not the path on the host machine.

In a way that ARS uses this, we keep the config, topo and data on one location as the files are fairly
small. The output then is put in another location as it file size can be much larger. To facilitate
this, mount the input and output data separately and modify the configuration paths.

.. code:: console

    docker run -v <input>:/data/input -v <output>:/data/output usdaarsnwrc/smrf run_smrf <path to config>