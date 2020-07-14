Run SMRF
========

After installing SMRF, generating a topo and creating a configuration file, SMRF can be ran. There are
two ways to run SMRF, first is through the ``run_smrf`` command or through the SMRF API. If SMRF is being
used as input to a snow or hydrology model, we recommend to use ``run_smrf`` as it will generate all
the input required.

``run_smrf`` command
--------------------

To run a full simulation simply run (barring any errors):

.. code:: bash

    run_smrf <config_file_path>


SMRF API
--------

The ``smrf`` package can also be used as an API, typically to focus on a single variable. There are steps that
SMRF uses to load the data then distribute and usage of the API should follow the same pattern. For example,
below is the function :mod:`run_smrf <smrf.framework.model_framework.run_smrf>`.

.. code:: python

    with SMRF(config) as s:
        # load topo data
        s.loadTopo()

        # initialize the distribution
        s.create_distribution()

        # initialize the outputs if desired
        s.initializeOutput()

        # load weather data  and station metadata
        s.loadData()

        # distribute
        s.distributeData()


The next example below builds on above and will distribute air temperature and vapor pressure. They can be used to
get the distributed dew point or web bulb temperature.

.. code:: python

    configFile = 'config.ini'

    with smrf.framework.SMRF(configFile) as s:

        # ===================================================================
        # Model setup and initialize
        # ===================================================================

        # These are steps that will load the necessary data and initialize
        # the framework. Once loaded, this shouldn't need to be re-ran except
        # if something major changes

        # load topo data
        s.loadTopo()

        # Create the distribution class
        s.distribute['air_temp'] = smrf.distribute.air_temp.ta(
            s.config['air_temp'])
        s.distribute['vapor_pressure'] = smrf.distribute.vapor_pressure.vp(
            s.config['vapor_pressure'])

        # load weather data  and station metadata
        s.loadData()

        # Initialize the distribution
        for v in s.distribute:
            s.distribute[v].initialize(s.topo, s.data)

        # initialize the outputs if desired
        s.initializeOutput()

        # Distribute the data and output
        for output_count, t in enumerate(s.date_time):

            s.distribute['air_temp'].distribute(s.data.air_temp.ix[t])
            s.distribute['vapor_pressure'].distribute(
                s.data.vapor_pressure.ix[t],
                s.distribute['air_temp'].air_temp)

            # output at the frequency and the last time step
            if (output_count % s.config['output']['frequency'] == 0) or \
                    (output_count == len(s.date_time)):
                s.output(t)