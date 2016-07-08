
Configuration
=============

SMRF is configured using a configuration file and an extention of Pythons 
`ConfigParser`_ (:mod:`smrf.framework.model_framework.MyParser`). See 
``test_data/testConfig.ini`` for an example and read below for more information
on specific sections.

A brief introduction to a configuration file from the `ConfigParser`_ documentation: ::

   The configuration file consists of sections, led by a [section] header and followed 
   by name: value entries, with continuations in the style of RFC 822 (see section 
   3.1.1, “LONG HEADER FIELDS”); name=value is also accepted. Note that leading 
   whitespace is removed from values. The optional values can contain format strings 
   which refer to other values in the same section, or values in a special DEFAULT 
   section. Additional defaults can be provided on initialization and retrieval. Lines 
   beginning with '#' or ';' are ignored and may be used to provide comments.
    
   Configuration files may include comments, prefixed by specific characters (# and ;). 
   Comments may appear on their own in an otherwise empty line, or may be entered in 
   lines holding values or section names. In the latter case, they need to be preceded 
   by a whitespace character to be recognized as a comment. (For backwards compatibility, 
   only ; starts an inline comment, while # does not.)

Section and keys are case insensitive.

*All values below are required exept those with default values, shown in
parenthesis next to the variable.*


Time
----

The time sections provides SMRF with the information about when to run. The date time
values can be anything that ``pandas.to_datetime()`` can parse. 

time_step
   Time step in minutes to run the model, should be the same as the data's time step
   
start_date
   SMRF start time, data will be truncated to start date
   
end_date
   SMRF end time, data will be truncated to end date
   
time_zone (default = UTC)
   Time zone for all times provided and how the model will be run
   see `pytz docs <http://pytz.sourceforge.net/>`_ for information on what is accepted

Example ::
   
   [time]
   TiMe_SteP:  60
   start_date: 2008-10-21 06:00
   end_date:   2008-10-23 06:00
   time_zone:  UTC   


Topo
----

All files that SMRF reads in the topo section are IPW images, for now.
You can convert an ASCII grid to an IPW image using the IPW command
``text2ipw``.  The DEM must have geoheadrs set as SMRF reads in the headers
to create the coordinate system. All files should have the same domain size.

dem
   The digital elevation model (DEM) for the basin
   
mask
   A mask of the water shed is used to calculate trends, not mask generated data
   
.. _veg_type:

veg_type
   Vegetation type as an integer, can be from any source
   
veg_height
   Height of vegetation
   
veg_k
   Vegetation extenction coefficient, see Link and Marks 1999
   
veg_tau
   Vegetation transmissivity, see Link and Marks 1999
   
basin_lat
   The latitude of the middle of the basin, used for calculating sun angle

basin_lon
   The longitude of the middle of the basin, used for calculating sun angle   

Example ::

   [TOPO]
   dem:        test_data/topo/dem.ipw
   mask:       test_data/topo/mask.ipw
   veg_type:   test_data/topo/veg_type.ipw
   veg_height: test_data/topo/veg_height.ipw
   veg_k:      test_data/topo/veg_k.ipw
   veg_tau:    test_data/topo/veg_tau.ipw
   
   basin_lat:  43.8639
   basin_lon:  -115.3333
   
   

Data Import
-----------

The data import sections tell SMRF where the station measurements shoud
come from.  Currently two methods are implemented, reading from CSV files or
from a MySQL database.  More information on the input data can be found in
the `input data <input_data.html>`_ page.


Stations
````````

The stations section tells SMRF what stations to use when loading data. Stations
will perform differently for each method.  

stations
   * Will always take precedence over client
   * Comma seperated list
   * For CSV files, the stations imported will be filtered to those specified
   * MySQL will only select data for these stations
   
client
   * Does not apply for CSV files
   * Will load all stations with client=value from the specified ``station_table`` below
   
Example ::

   [stations]
   stations:   ATAI1,BOII,BNRI1,VNNI1,TRMI1,BOGI1,TR216
   client:     BRB


CSV Data
````````

Each variable will have it's own CSV file with rows representing time and 
columns representing the stations.  See `input data <input_data.html>`_ for
a more in depth description for formulating the files.

metadata
   The station metadata for station id, location and elevation

air_temp
   Air temperature file
   
vapor_pressure
   Vapor pressure file
   
precip
   Precipitation file
   
wind_speed
   Wind speed file
   
wind_direction
   Wind direction file
   
cloud_factor
   Cloud factor file
   
Example ::

   [csv]
   metadata:         test_data/stationData/ta_metadata.csv
   air_temp:         test_data/stationData/final_air_temp.csv
   vapor_pressure:   test_data/stationData/final_vp.csv
   precip:           test_data/stationData/final_precip.csv
   wind_speed:       test_data/stationData/final_wind_speed.csv
   wind_direction:   test_data/stationData/final_wind_dir.csv
   cloud_factor:     test_data/stationData/final_cf.csv


MySQL Database
``````````````

The MySQL section provides connection information for the database, 
the table to pull data from, and what the column names are for each variable.

user
   MySQL database user
   
password
   MySQL database user password
   
host
   MySQL server IP address, typically localhost (127.0.0.1) if database
   is on the local computer
   
database
   MySQL database name
   
metadata
   Table name that contains the station metadata
   
data_table
   Table name that contains all the station data
  
station_table
   Station table only required if using [stations]client
   
air_temp
   Column name for air temperature variable
   
vapor_pressure
   Column name for vapor pressure variable
   
precip
   Column name for precipitation variable
   
wind_speed
   Column name for wind speed variable
   
wind_direction
   Column name for wind direction variable
   
cloud_factor
   Column name for cloud factor variable
   
Example ::

   [mysql]
   user:             user
   password:         password
   host:             localhost
   database:         db_name
   metadata:         tbl_metadata
   data_table:       tbl_data
   station_table:    tbl_stations
   air_temp:         air_temp
   vapor_pressure:   vapor_pressure
   precip:           precip_accum
   wind_speed:       wind_speed
   wind_direction:   wind_direction
   cloud_factor:     cloud_factor


.. _dist-methods:

Distribution methods
--------------------

The distribution parameter will tell SMRF how to distribute each variable if
required. Different options exist depending on the distribution selected.  Currently
two distribution techniques are implemented, inverse distance weighting and 
detrended kriging.  More information on the distribution methods can be 
found in the `distribution methods <dist_methods.html>`_ page.


Inverse Distance Weighting
``````````````````````````

When inverse distance weighting is selected, an option exist to detrend
the distribution by elevation, distribute the residuals, and retrend to
elevation. The slope can be specified to constrain the fit.

distribution: idw
   idw for inverse distance weighting
   
detrend (default = false)
   defaults to false, true will detrend before distributing
   
slope (default = 0)
   if detrend is true, constain the slope to positive (1), negative (-1), 
   or no constraint (0, default)
   
Example ::

   distribution:  idw
   detrend:       true
   slope:         -1


Detrended Kriging
`````````````````

Select detrended kriging for the distribution method will follow the methods
developed by Garen and Marks, 2005.  

distribution: dk
   dk for detrended kriging
   
slope (default = 0)
   Constain the slope to positive (1), negative (-1), or no constraint (0, default)
   
dk_nthreads (default = 1)
   Number of processors to use in the kriging calculation
   
Example ::

   distribution:  dk
   slope:         -1
   dk_nthreads:   12


Variable configuration
----------------------

Each variable can further filter the stations to use and with what method 
to use for distribution. More information on the variable calculations can
be found in the `API documentation <api.html>`_ for that variables module.

All variables have the following parameters:

stations
   If set, only these stations will be used, else all possible stations
   that were loaded will be used

Air temperature
```````````````

Takes the ``air_temp`` data and distributes using :mod:`smrf.distribute.air_temp`

distribution
   :ref:`Distribution method <dist-methods>` with other parameters

Example ::

   [air_temp]
   
   stations:         ATAI1,BNRI1,VNNI1,TRMI1,BOGI1,TR216
   distribution:     idw
   detrend:          true
   slope:            -1


Vapor pressure
``````````````

Distribute ``vapor_pressure`` data using :mod:`smrf.distribute.vapor_pressure`. 
The module also calculates the dew point temperature for estimating 
precipitation phase.

distribution
   :ref:`Distribution method <dist-methods>` with other parameters
   
tolerance
   Convergence tolerance in dew point calculation
   
nthread
   Number of processors to use in dew point calculation
   
Example ::
   [vapor_pressure]
   
   stations:         BNRI1,BOGI1,ATAI1,TR216
   distribution:     idw
   detrend:          true  
   slope:            -1
   tolerance:        0.01
   nthreads:         6  


Wind speed and direction
````````````````````````

Distributes wind speed and direction using :mod:`smrf.distribute.wind`.
The wind direction distributes the ``wind_direction`` data using the 
specified distribution method. Wind speed is estimated using the methods
developed by Winstral et al, 2002. The maxus value at each station can be
enhanced as well as specifying if the station is on a highpoint (peak) which
will observe higher wind speeds.  Vegetation enhancements are also
specified base on the integer value in the :ref:`veg_type<veg_type>` image.


distribution
   :ref:`Distribution method <dist-methods>` with other parameters, distributes
   the wind direction
   
maxus_netcdf
   maxus NetCDF with 'maxus' variable, see :mod:`smrf.utils.wind_model`
   
station_id: enhancement_value
   Each station can have its own enhancement value specified as a name: value
   pair.  
   
station_default
   Applies the value to all stations not specified.
   
peak
   Comma seperated list of stations that are on a peak or highpoint.  The
   minimum maxus  value of all directions will be used to ensure that the
   wind speeds are within reason
   
veg_default
   Applies the value to all vegetation not specified
   
veg_(integer)
   Integer represents the value in the :ref:`veg_type<veg_type>` image
 
reduction_factor
   If wind speeds are still off, here is a scaling factor
   
Example ::

   [wind]
   stations:         TR216,VNNI1,ATAI1
   distribution:     idw
   detrend:          false
   maxus_netcdf:     test_data/topo/maxus.nc
   
   # enhancement for each site
   TR216:            0
   VNNI1:            3.0   
   ATAI1:            5.0
   station_default:  11.4
   
   peak:             TR216 
            
   # enhancement for vegetation
   veg_default:      11.4
   veg_41:           11.4
   veg_42:           11.4
   veg_43:           3.3
   
   reduction_factor: 0.7   

Precipitation
`````````````

Distributes the ``precip`` data using :mod:`smrf.distribute.precipitation`.

distribution
   :ref:`Distribution method <dist-methods>` with other parameters
   
Example::

   [precip]
   stations:         BNRI1,BOGI1,ATAI1,TRMI1,VNNI1
   distribution:     dk
   slope:            -1
   dk_nthreads:      12

Albedo
``````

No distribution is performed for albedo as it uses the distributed
precipitation to estimate time since last storm.  The following set the
parameters for the albedo calculation.

grain_size (default = 300)
   Effective grain radius of snow after last storm (mu m)
   
max_grain (default = 2000)
   Maximum grain radius expected from grain growth (mu m)
   
dirt (default = 2.0)
   Effective contamination for adjustment to visible albedo (usually between 1.5-3.0)

Example ::

   [albedo]
   grain_size:    300
   max_grain:     2000
   dirt:          2.0


Solar
`````

Distributes the ``cloud_factor`` data using :mod:`smrf.distribute.solar`.
Specify atmosphic parameters for calculating the clear sky radiation

distribution
   :ref:`Distribution method <dist-methods>` with other parameters
   
clear_opt_depth (default = 100)
   Elevation of optical depth measurement

clear_tau (default = 0.2)
   optical depth at z
   
clear_omega (default = 0.85)
   Single-scattering albedo

clear_gamma (default = 0.3)
   Scattering asymmetry parameter

Thermal
```````

Thermal requires no distribution methods.

nthreads
   Number of processors to calculate clear sky thermal radiation
   
Example ::

   [thermal]
   nthreads:      4
   

Soil temperature
````````````````

Soil temperature requires no distribution methods.

temp
   soil temperature value
   
Example ::

   [soil_temp]
   temp:       -2.5


Output
------

Specify variable output frequency, variables, and what file type.

frequency
   Frequency in time step that should be written to disk
   
out_location
   Location to put the files
   
variables
   Comma seperated list of variables to output
   
file_type
   Type of file to output, currently only netcdf is implemented
   
Example ::

   [output]
   frequency:     1 
   out_location:  ~/Desktop/test/   
   variables:     thermal, air_temp, vapor_pressure, wind_speed, net_solar, precip
   file_type:     netcdf

Logging
-------

SMRF using Python's `logging`_ module
to output relevant information about SMRF processes.

log_level
   info, debug, warn, or error
   
log_file
   If specified, will log to a file, if not, then will log to console
   
Example ::

   [logging]
   log_level:     debug
   log_file:      log.out

System variables
----------------

System variables to specify some special options for SMRF.

temp_dir
   Location to put working files, if not specified will attempt to use
   the environment variable TMPDIR
   
threading
   Whether or not to use threading and data queues to store variables. Each
   variable will be on it's own thread operating independently of other threads
   but putting and getting data from the queue
   
max_values
   Maximum number of time steps to keep in the data queue
   
Example ::

   [system]
   temp_dir:      /tmp
   threading:     true
   max_values:    2



.. _ConfigParser: https://docs.python.org/2/library/configparser.html
.. _logging: https://docs.python.org/2/library/logging.html