Create a config file
====================

After the topo file has been created, build the SMRF configuration file. For in depth documentation
see how to :doc:`use a configuration file <../user_guide/configuration>` and the
:doc:`core configuration <../user_guide/core_config>` for all SMRF options.

.. note::

    Configuration file paths are relative to the configuration file location.

At a minimum to get started, the following configuration file will apply all the defaults.
The required changes are specifying the path to the ``topo.nc`` file, dates to run the model
and the location of the csv input data.


.. code::

    ################################################################################
    # Files for DEM and vegetation
    ################################################################################
    [topo]
    filename:                      ./topo/topo.nc

    ################################################################################
    # Dates to run model
    ################################################################################
    [time]
    time_step:                     60
    start_date:                    1998-01-14 15:00:00
    end_date:                      1998-01-14 19:00:00
    time_zone:                     utc

    ################################################################################
    # CSV section configurations
    ################################################################################
    [csv]
    wind_speed:                    ./station_data/wind_speed.csv
    air_temp:                      ./station_data/air_temp.csv
    cloud_factor:                  ./station_data/cloud_factor.csv
    wind_direction:                ./station_data/wind_direction.csv
    precip:                        ./station_data/precip.csv
    vapor_pressure:                ./station_data/vapor_pressure.csv
    metadata:                      ./station_data/metadata.csv

    ################################################################################
    # Air temperature distribution
    ################################################################################
    [air_temp]

    ################################################################################
    # Vapor pressure distribution
    ################################################################################
    [vapor_pressure]

    ################################################################################
    # Wind speed and wind direction distribution
    ################################################################################
    [wind]
    maxus_netcdf:                  ./topo/maxus.nc

    ################################################################################
    # Precipitation distribution
    ################################################################################
    [precip]

    ################################################################################
    # Albedo distribution
    ################################################################################
    [albedo]

    ################################################################################
    # Cloud Factor - Fraction used to limit solar radiation Cloudy (0) - Sunny (1)
    ################################################################################
    [cloud_factor]

    ################################################################################
    # Solar radiation
    ################################################################################
    [solar]

    ################################################################################
    # Incoming thermal radiation
    ################################################################################
    [thermal]

    ################################################################################
    # Soil temperature
    ################################################################################
    [soil_temp]

    ################################################################################
    # Output variables
    ################################################################################
    [output]
    out_location:                  ./output

    ################################################################################
    # System variables and Logging
    ################################################################################
    [system]

