Core Configuration
==================
Adding variables and options to the SMRF configuration file is now easily managed
by a single master configuration file stored in the repo under ./smrf/framework/CoreConfig.ini.
Through this the users config file can now be checked against all the options available.

When developing and adding features to SMRF please follow this convention.
* Each configuration added should be added under its respective section.
* Every variable that is changeable should be listed in the configurable item as comma separated.
This is required if the user wants to use it.
* If the has specific string options, they should be provided under the available_options item.
The options should already exist in the configurable item and it options should be listed in a bracketed space separated list.
* If you have provided a new option it should be provided a default. They are described by the configurable separated by a =.

See the following example.

Example ::

  [precipitation]
    configurable: my_rain_model, new_snow_parameter
    available_options: my_rain_model = [curly mo larry], new_snow_parameter=[sharknado antman]
    default: new_rain_model=Larry, new_snow_parameter=sharknado

This would add two new configurable options called my_rain_model and new snow_parameter.
They would only be able to be set to  curly,mo and larry for the my_rain_model and for the
the new_snow_parameter sharknado and antman. Each has a default in the event it is
not specified by the user which in this case is Larry and sharknado respectively.
The CoreConfiguration also allows the user to specify the type to further constrain the inputs.
For example:
Example ::

  [precipitation]
    configurable: min, storm_days_restart
    available_options: min = <float>, storm_days_restart=<filename>
    
This would force the user to put in a type float for the min and a real filename for the storm_days_restart.
Even though a real list of options was not provided SMRF will check to make sure the the user adheres to
the specified requirements. If no type if provided at all, SMRF will assume it is a string.
Available types are:
* datetime
* str
* bool
* int
* float
* filename
* directory

