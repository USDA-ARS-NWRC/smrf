
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