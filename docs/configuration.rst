
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

*All values below are required exept those with default values.*


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
   
time_zone (default UTC)
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



Stations
````````

CSV Data
````````

MySQL Database
``````````````

Distribution methods
--------------------

Inverse Distance Weighting
``````````````````````````

Detrended Kriging
`````````````````


Variable configuration
----------------------

Air temperature
```````````````

Vapor pressure
``````````````

Wind speed and direction
````````````````````````

Precipitation
`````````````

Albedo
``````

Solar
`````

Thermal
```````

Soil temperature
````````````````

Output
------

Logging
-------


System variables
----------------




.. _ConfigParser: https://docs.python.org/2/library/configparser.html