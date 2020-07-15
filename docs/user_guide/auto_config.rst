
For configuration file syntax information please visit http://inicheck.readthedocs.io/en/latest/


topo
----

| **filename**
| 	A netCDF file containing all veg info and dem.
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **gradient_method**
| 	Method to use for calculating the slope and aspect. gradient_d8 uses 3 by 3 finite difference window and gradient_d4 uses a two cell finite difference for x and y
| 		*Default: gradient_d8*
| 		*Type: string*
| 		*Options:*
 *gradient_d8 gradient_d4*
| 

| **northern_hemisphere**
| 	Boolean describing whether the model domain is in the northern hemisphere or not
| 		*Default: True*
| 		*Type: bool*
| 

| **sky_view_factor_angles**
| 	Number of directions to estimate the horizon. Divides 360 degrees into evenly spaced directions.
| 		*Default: 72*
| 		*Type: int*
| 


time
----

| **end_date**
| 	Date and time to end the data distribution that can be parsed by pandas.to_datetime
| 		*Default: None*
| 		*Type: datetimeorderedpair*
| 

| **start_date**
| 	Date and time to start the data distribution that can be parsed by pandas.to_datetime
| 		*Default: None*
| 		*Type: datetimeorderedpair*
| 

| **time_step**
| 	Time interval that SMRF distributes data at in minutes
| 		*Default: 60*
| 		*Type: int*
| 

| **time_zone**
| 	Case sensitive time zone for all times provided and how the model will be run. See pytz docs for information on what is accepted. Full list can be found en.wikipedia.org/wiki/List_of_tz_database_time_zones
| 		*Default: UTC*
| 		*Type: rawstring*
| 


csv
---

| **air_temp**
| 	Path to CSV containing the station measured air temperature
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **cloud_factor**
| 	Path to CSV containing the station measured cloud factor
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **metadata**
| 	Path to CSV containing the station metadata
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **precip**
| 	Path to CSV containing the station measured precipitation
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **stations**
| 	List of station IDs to use for distributing any of the variables
| 		*Default: None*
| 		*Type: station*
| 

| **vapor_pressure**
| 	Path to CSV containing the station measured vapor pressure
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **wind_direction**
| 	Path to CSV containing the station measured wind direction
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **wind_speed**
| 	Path to CSV containing the station measured wind speed
| 		*Default: None*
| 		*Type: criticalfilename*
| 


gridded
-------

| **data_type**
| 	Type of gridded input data
| 		*Default: hrrr_grib*
| 		*Type: string*
| 		*Options:*
 *wrf hrrr_grib netcdf*
| 

| **hrrr_directory**
| 	Path to the top level directory where multiple HRRR gridded dataset are located
| 		*Default: None*
| 		*Type: criticaldirectory*
| 

| **hrrr_forecast_flag**
| 	True if the HRRR data is a forecast
| 		*Default: False*
| 		*Type: bool*
| 

| **hrrr_load_method**
| 	Method to load the HRRR data either load all data first or for each timestep
| 		*Default: first*
| 		*Type: string*
| 		*Options:*
 *first timestep*
| 

| **netcdf_file**
| 	Path to the netCDF file containing weather data
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **wrf_file**
| 	Path to the netCDF file containing WRF data
| 		*Default: None*
| 		*Type: criticalfilename*
| 


air_temp
--------
The air_temp section controls all the available parameters that effect the distribution of the air_temp module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.air_temp`

| **detrend**
| 	Whether to elevationally detrend prior to distributing
| 		*Default: true*
| 		*Type: bool*
| 

| **detrend_slope**
| 	If detrend is true constrain the detrend_slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: -1*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **distribution**
| 	Distribution method to use for <this variable>. Stations use dk idw or kriging. Gridded data use grid. Stations use dk idw or kriging. Gridded data use grid.
| 		*Default: idw*
| 		*Type: string*
| 		*Options:*
 *dk idw grid kriging*
| 

| **dk_ncores**
| 	Number of threads or processors to use in the dk calculation
| 		*Default: 1*
| 		*Type: int*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	Gridded interpolation method to use for air temperature
| 		*Default: cubic*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **idw_power**
| 	Power for decay of a stations influence in inverse distance weighting.
| 		*Default: 2.0*
| 		*Type: float*
| 

| **krig_anisotropy_angle**
| 	CCW angle (in degrees) by which to rotate coordinate system in order to take into account anisotropy.
| 		*Default: 0.0*
| 		*Type: float*
| 

| **krig_anisotropy_scaling**
| 	Scalar stretching value for kriging to take into account anisotropy.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **krig_coordinates_type**
| 	Determines if the x and y coordinates are interpreted as on a plane (euclidean) or as coordinates on a sphere (geographic).
| 		*Default: euclidean*
| 		*Type: string*
| 		*Options:*
 *euclidean geographic*
| 

| **krig_nlags**
| 	Number of averaging bins for the kriging semivariogram
| 		*Default: 6*
| 		*Type: int*
| 

| **krig_variogram_model**
| 	Specifies which kriging variogram model to use
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *linear power gaussian spherical exponential hole-effect*
| 

| **krig_weight**
| 	Flag that specifies if the kriging semivariance at smaller lags should be weighted more heavily when automatically calculating variogram model.
| 		*Default: False*
| 		*Type: bool*
| 

| **max**
| 	Maximum possible value for air temperature in Celsius
| 		*Default: 47.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible value for air temperature in Celsius
| 		*Default: -73.0*
| 		*Type: float*
| 

| **stations**
| 	Stations to use for distributing air temperature
| 		*Default: None*
| 		*Type: station*
| 


vapor_pressure
--------------
The vapor_pressure section controls all the available parameters that effect the distribution of the vapor_pressure module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.vapor_pressure`

| **detrend**
| 	Whether to elevationally detrend prior to distributing
| 		*Default: true*
| 		*Type: bool*
| 

| **detrend_slope**
| 	If detrend is true constrain the slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: -1*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **dew_point_nthreads**
| 	Number of threads to use in the dew point calculation
| 		*Default: 2*
| 		*Type: int*
| 

| **dew_point_tolerance**
| 	Solving criteria for the dew point calculation
| 		*Default: 0.01*
| 		*Type: float*
| 

| **distribution**
| 	Distribution method to use for vapor pressure. Stations use dk idw or kriging. Gridded data use grid.
| 		*Default: idw*
| 		*Type: string*
| 		*Options:*
 *dk idw grid kriging*
| 

| **dk_ncores**
| 	Number of threads to use in the dk calculation
| 		*Default: 1*
| 		*Type: int*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	interpolation method to use for this variable
| 		*Default: cubic*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **idw_power**
| 	Power for decay of a stations influence in inverse distance weighting
| 		*Default: 2.0*
| 		*Type: float*
| 

| **krig_anisotropy_angle**
| 	CCW angle (in degrees) by which to rotate coordinate system in order to take into account anisotropy.
| 		*Default: 0.0*
| 		*Type: float*
| 

| **krig_anisotropy_scaling**
| 	Scalar stretching value for kriging to take into account anisotropy.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **krig_coordinates_type**
| 	Determines if the x and y coordinates are interpreted as on a plane (euclidean) or as coordinates on a sphere (geographic).
| 		*Default: euclidean*
| 		*Type: string*
| 		*Options:*
 *euclidean geographic*
| 

| **krig_nlags**
| 	Number of averaging bins for the kriging semivariogram
| 		*Default: 6*
| 		*Type: int*
| 

| **krig_variogram_model**
| 	Specifies which kriging variogram model to use
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *linear power gaussian spherical exponential hole-effect*
| 

| **krig_weight**
| 	Flag that specifies if the kriging semivariance at smaller lags should be weighted more heavily when automatically calculating variogram model.
| 		*Default: False*
| 		*Type: bool*
| 

| **max**
| 	Maximum possible vapor pressure in Pascals
| 		*Default: 5000.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible vapor pressure in Pascals
| 		*Default: 20.0*
| 		*Type: float*
| 

| **stations**
| 	Stations to use for distributing vapor pressure in Pascals
| 		*Default: None*
| 		*Type: station*
| 


wind
----
The wind section controls all the available parameters that effect the distribution of the wind module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.wind`

| **detrend**
| 	Whether to elevationally detrend prior to distributing
| 		*Default: False*
| 		*Type: bool*
| 

| **detrend_slope**
| 	if detrend is true constrain the detrend_slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: 1*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **distribution**
| 	Distribution method to use for wind. Stations use dk idw or kriging. Gridded data use grid.
| 		*Default: idw*
| 		*Type: string*
| 		*Options:*
 *dk idw grid kriging*
| 

| **dk_ncores**
| 	Number of threads to use in the dk calculation
| 		*Default: 2*
| 		*Type: int*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	Number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	interpolation method to use for wind
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **idw_power**
| 	Power for decay of a stations influence in inverse distance weighting
| 		*Default: 2.0*
| 		*Type: float*
| 

| **krig_anisotropy_angle**
| 	CCW angle (in degrees) by which to rotate coordinate system in order to take into account anisotropy.
| 		*Default: 0.0*
| 		*Type: float*
| 

| **krig_anisotropy_scaling**
| 	Scalar stretching value for kriging to take into account anisotropy.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **krig_coordinates_type**
| 	Determines if the x and y coordinates are interpreted as on a plane (euclidean) or as coordinates on a sphere (geographic).
| 		*Default: euclidean*
| 		*Type: string*
| 		*Options:*
 *euclidean geographic*
| 

| **krig_nlags**
| 	Number of averaging bins for the kriging semivariogram
| 		*Default: 6*
| 		*Type: int*
| 

| **krig_variogram_model**
| 	Specifies which kriging variogram model to use
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *linear power gaussian spherical exponential hole-effect*
| 

| **krig_weight**
| 	Flag that specifies if the kriging semivariance at smaller lags should be weighted more heavily when automatically calculating variogram model.
| 		*Default: False*
| 		*Type: bool*
| 

| **max**
| 	Maximum possible wind in M/s
| 		*Default: 35.0*
| 		*Type: float*
| 

| **maxus_netcdf**
| 	NetCDF file containing the maxus values for wind
| 		*Default: None*
| 		*Type: criticalfilename*
| 

| **min**
| 	Minimum possible for wind in M/s
| 		*Default: 0.447*
| 		*Type: float*
| 

| **reduction_factor**
| 	If wind speeds are still off here is a scaling factor
| 		*Default: 1.0*
| 		*Type: float*
| 

| **station_default**
| 	Account for sheltered station wind measurements for example 11.4 equates to a small forest opening and 0 equates to unsheltered measurements.
| 		*Default: 11.4*
| 		*Type: float*
| 

| **station_peak**
| 	Name of stations that lie on a peak or a high point
| 		*Default: None*
| 		*Type: station*
| 

| **stations**
| 	Stations to use for distributing wind in M/s
| 		*Default: None*
| 		*Type: station*
| 

| **veg_3011**
| 	Applies the value where vegetation equals 3011(Rocky Mountain aspen)
| 		*Default: 3.3*
| 		*Type: float*
| 

| **veg_3061**
| 	Applies the value where vegetation equals 3061(mixed aspen)
| 		*Default: 3.3*
| 		*Type: float*
| 

| **veg_41**
| 	Applies the value where vegetation type equals NLCD class 41
| 		*Default: 3.3*
| 		*Type: float*
| 

| **veg_42**
| 	Applies the value where vegetation type equals NLCD class 42
| 		*Default: 3.3*
| 		*Type: float*
| 

| **veg_43**
| 	Applies the value where vegetation type equals NLCD class 43
| 		*Default: 11.4*
| 		*Type: float*
| 

| **veg_default**
| 	Applies the value to all vegetation not specified
| 		*Default: 0.0*
| 		*Type: float*
| 

| **wind_model**
| 	Wind model to interpolate wind measurements to the model domain
| 		*Default: winstral*
| 		*Type: string*
| 		*Options:*
 *winstral wind_ninja interp*
| 

| **wind_ninja_dir**
| 	Location in which the ascii files are output from the WindNinja simulation. This serves as a trigger for checking for WindNinja files.
| 		*Default: None*
| 		*Type: criticaldirectory*
| 

| **wind_ninja_dxdy**
| 	grid spacing at which the WindNinja ascii files are output.
| 		*Default: 100*
| 		*Type: int*
| 

| **wind_ninja_height**
| 	The output height of wind fields from WindNinja in meters.
| 		*Default: 5.0*
| 		*Type: string*
| 

| **wind_ninja_pref**
| 	Prefix of all outputs from WindNinja that matches the topo input to WindNinja.
| 		*Default: None*
| 		*Type: string*
| 

| **wind_ninja_roughness**
| 	The surface roughness used in WindNinja generally grass.
| 		*Default: 0.01*
| 		*Type: string*
| 

| **wind_ninja_tz**
| 	Time zone that from the WindNinja config.
| 		*Default: UTC*
| 		*Type: string*
| 


precip
------
The precipitation section controls all the available parameters that effect the distribution of the precipitation module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.precipitation`

| **detrend**
| 	Whether to elevationally detrend prior to distributing
| 		*Default: true*
| 		*Type: bool*
| 

| **detrend_slope**
| 	if detrend is true constrain the detrend_slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: 1*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **distribution**
| 	Distribution method to use for precipitation. Stations use dk idw or kriging. Gridded data use grid.
| 		*Default: dk*
| 		*Type: string*
| 		*Options:*
 *dk idw grid kriging*
| 

| **dk_ncores**
| 	Number of threads to use in the dk calculation
| 		*Default: 2*
| 		*Type: int*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	interpolation method to use for precipitation
| 		*Default: cubic*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **idw_power**
| 	Power for decay of a stations influence in inverse distance weighting
| 		*Default: 2.0*
| 		*Type: float*
| 

| **krig_anisotropy_angle**
| 	CCW angle (in degrees) by which to rotate coordinate system in order to take into account anisotropy.
| 		*Default: 0.0*
| 		*Type: float*
| 

| **krig_anisotropy_scaling**
| 	Scalar stretching value for kriging to take into account anisotropy.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **krig_coordinates_type**
| 	Determines if the x and y coordinates are interpreted as on a plane (euclidean) or as coordinates on a sphere (geographic).
| 		*Default: euclidean*
| 		*Type: string*
| 		*Options:*
 *euclidean geographic*
| 

| **krig_nlags**
| 	Number of averaging bins for the kriging semivariogram
| 		*Default: 6*
| 		*Type: int*
| 

| **krig_variogram_model**
| 	Specifies which kriging variogram model to use
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *linear power gaussian spherical exponential hole-effect*
| 

| **krig_weight**
| 	Flag that specifies if the kriging semivariance at smaller lags should be weighted more heavily when automatically calculating variogram model.
| 		*Default: False*
| 		*Type: bool*
| 

| **marks2017_timesteps_to_end_storms**
| 	number of timesteps to elapse with precip under start criteria before ending a storm.
| 		*Default: 6*
| 		*Type: int*
| 

| **max**
| 	Maximum possible precipitation in millimeters
| 		*Default: None*
| 		*Type: float*
| 

| **min**
| 	Minimum possible for precipitation in millimeters
| 		*Default: 0.0*
| 		*Type: float*
| 

| **new_snow_density_model**
| 	Method to use for calculating the new snow density
| 		*Default: susong1999*
| 		*Type: string*
| 		*Options:*
 *marks2017 susong1999 piecewise_susong1999*
| 

| **precip_rescaling_model**
| 	Method to use for redistributing precipitation. Winstrals method focuses forming drifts from wind
| 		*Default: None*
| 		*Type: string*
| 		*Options:*
 *winstral*
| 

| **precip_temp_method**
| 	which variable to use for precip temperature
| 		*Default: dew_point*
| 		*Type: string*
| 		*Options:*
 *dew_point wet_bulb*
| 

| **station_adjust_for_undercatch**
| 	Apply undercatch relationships to precip gauges
| 		*Default: true*
| 		*Type: bool*
| 

| **station_undercatch_model_default**
| 	WMO model used to adjust for undercatch of precipitaiton
| 		*Default: us_nws_8_shielded*
| 		*Type: string*
| 		*Options:*
 *us_nws_8_shielded us_nws_8_unshielded*
| 

| **stations**
| 	Stations to use for distributing this precipitation
| 		*Default: None*
| 		*Type: station*
| 

| **storm_days_restart**
| 	Path to netcdf representing the last storm days so a run can continue in between stops
| 		*Default: None*
| 		*Type: discretionarycriticalfilename*
| 

| **storm_mass_threshold**
| 	Start criteria for a storm in mm of measured precipitation in millimeters in any pixel over the domain.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **susong1999_timesteps_to_end_storms**
| 	number of timesteps to elapse with precip under start criteria before ending a storm.
| 		*Default: 6*
| 		*Type: int*
| 

| **winstral_max_drift**
| 	max multiplier for precip redistribution in a drift cell
| 		*Default: 3.5*
| 		*Type: float*
| 

| **winstral_max_scour**
| 	max multiplier for precip redistribution to account for wind scour.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **winstral_min_drift**
| 	min multiplier for precip redistribution in a drift cell
| 		*Default: 1.0*
| 		*Type: float*
| 

| **winstral_min_scour**
| 	minimum multiplier for precip redistribution to account for wind scour.
| 		*Default: 0.55*
| 		*Type: float*
| 

| **winstral_tbreak_netcdf**
| 	NetCDF file containing the tbreak values for wind
| 		*Default: None*
| 		*Type: filename*
| 

| **winstral_tbreak_threshold**
| 	Threshold for drift cells measured in degrees from tbreak file.
| 		*Default: 7.0*
| 		*Type: float*
| 

| **winstral_veg_3011**
| 	Interference inverse factor for precip redistribution where vegetation equals 3011(Rocky Mountain Aspen).
| 		*Default: 0.7*
| 		*Type: float*
| 

| **winstral_veg_3061**
| 	Interference inverse factor for precip redistribution where vegetation equals 3061(Mixed Aspen).
| 		*Default: 0.7*
| 		*Type: float*
| 

| **winstral_veg_41**
| 	Interference inverse factor for precip redistribution where vegetation equals 41.
| 		*Default: 0.7*
| 		*Type: float*
| 

| **winstral_veg_42**
| 	Interference inverse factor for precip redistribution where vegetation equals 42.
| 		*Default: 0.7*
| 		*Type: float*
| 

| **winstral_veg_43**
| 	Interference inverse factor for precip redistribution where vegetation equals 43.
| 		*Default: 0.7*
| 		*Type: float*
| 

| **winstral_veg_default**
| 	Applies the value to all vegetation not specified
| 		*Default: 1.0*
| 		*Type: float*
| 


albedo
------
The albedo section controls all the available parameters that effect the distribution of the albedo module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.albedo`

| **date_method_decay_power**
| 	Exponent value of the decay rate equation prescribed by the method.
| 		*Default: 0.714*
| 		*Type: float*
| 

| **date_method_end_decay**
| 	Starting date for applying the decay method described by date_method
| 		*Default: None*
| 		*Type: datetimeorderedpair*
| 

| **date_method_start_decay**
| 	Starting date for applying the decay method described by date_method
| 		*Default: None*
| 		*Type: datetimeorderedpair*
| 

| **date_method_veg_41**
| 	Applies the value where vegetation equals 41
| 		*Default: 0.36*
| 		*Type: float*
| 

| **date_method_veg_42**
| 	Applies the value where vegetation equals 42
| 		*Default: 0.36*
| 		*Type: float*
| 

| **date_method_veg_43**
| 	Applies the value where vegetation equals 43
| 		*Default: 0.25*
| 		*Type: float*
| 

| **date_method_veg_default**
| 	Applies the value to all vegetation not specified
| 		*Default: 0.25*
| 		*Type: float*
| 

| **decay_method**
| 	Describe how the albedo decays in the late season
| 		*Default: None*
| 		*Type: string*
| 		*Options:*
 * hardy2000 date_method none*
| 

| **dirt**
| 	Effective contamination for adjustment to visible albedo (usually between 1.5-3.0)
| 		*Default: 2.0*
| 		*Type: float*
| 

| **grain_size**
| 	Effective optical grain radius of snow after last storm in micro-meters
| 		*Default: 100.0*
| 		*Type: float*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **hardy2000_litter_albedo**
| 	Albedo of the litter on the snow using the hard method
| 		*Default: 0.2*
| 		*Type: float*
| 

| **hardy2000_litter_default**
| 	Litter rate for places where vegetation not specified for Hardy et al. 2000 decay method
| 		*Default: 0.003*
| 		*Type: float*
| 

| **hardy2000_litter_veg_41**
| 	Litter rate for places where vegetation not specified for Hardy et al. 2000 decay method for vegetation classes NLCD 41
| 		*Default: 0.006*
| 		*Type: float*
| 

| **hardy2000_litter_veg_42**
| 	Litter rate for places where vegetation not specified for Hardy et al. 2000 decay method for vegetation classes NLCD 42
| 		*Default: 0.006*
| 		*Type: float*
| 

| **hardy2000_litter_veg_43**
| 	Litter rate for places where vegetation not specified for Hardy et al. 2000 decay method for vegetation classes NLCD 43
| 		*Default: 0.003*
| 		*Type: float*
| 

| **max**
| 	Maximum possible for albedo
| 		*Default: 1.0*
| 		*Type: float*
| 

| **max_grain**
| 	Max optical grain radius of snow possible in micro-meters
| 		*Default: 700.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible for albedo
| 		*Default: 0.0*
| 		*Type: float*
| 


cloud_factor
------------
The cloud_factor section controls all the available parameters that effect the distribution of the cloud_factor module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.cloud_factor`

| **detrend**
| 	Whether to elevationally detrend prior to distributing
| 		*Default: false*
| 		*Type: bool*
| 

| **detrend_slope**
| 	If detrend is true constrain the detrend_slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: 0*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **distribution**
| 	Distribution method to use for cloud factor. Stations use dk idw or kriging. Gridded data use grid. Stations use dk idw or kriging. Gridded data use grid.
| 		*Default: idw*
| 		*Type: string*
| 		*Options:*
 *dk idw grid kriging*
| 

| **dk_ncores**
| 	Number of threads or processors to use in the dk calculation
| 		*Default: 1*
| 		*Type: int*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the distribution calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	Gridded interpolation method to use for cloud factor
| 		*Default: cubic*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **idw_power**
| 	Power for decay of a stations influence in inverse distance weighting.
| 		*Default: 2.0*
| 		*Type: float*
| 

| **krig_anisotropy_angle**
| 	CCW angle (in degrees) by which to rotate coordinate system in order to take into account anisotropy.
| 		*Default: 0.0*
| 		*Type: float*
| 

| **krig_anisotropy_scaling**
| 	Scalar stretching value for kriging to take into account anisotropy.
| 		*Default: 1.0*
| 		*Type: float*
| 

| **krig_coordinates_type**
| 	Determines if the x and y coordinates are interpreted as on a plane (euclidean) or as coordinates on a sphere (geographic).
| 		*Default: euclidean*
| 		*Type: string*
| 		*Options:*
 *euclidean geographic*
| 

| **krig_nlags**
| 	Number of averaging bins for the kriging semivariogram
| 		*Default: 6*
| 		*Type: int*
| 

| **krig_variogram_model**
| 	Specifies which kriging variogram model to use
| 		*Default: linear*
| 		*Type: string*
| 		*Options:*
 *linear power gaussian spherical exponential hole-effect*
| 

| **krig_weight**
| 	Flag that specifies if the kriging semivariance at smaller lags should be weighted more heavily when automatically calculating variogram model.
| 		*Default: False*
| 		*Type: bool*
| 

| **max**
| 	Max prossible cloud factor as a decimal representing full clouds (0) to full sun (1).
| 		*Default: 1.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible cloud factor as a decimal representing full clouds (0) to full sun (1).
| 		*Default: 0.0*
| 		*Type: float*
| 

| **stations**
| 	Stations to use for distributing cloud factor as a decimal representing full clouds (0) to full sun (1).
| 		*Default: None*
| 		*Type: station*
| 


solar
-----
The solar section controls all the available parameters that effect the distribution of the solar module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.solar`

| **clear_gamma**
| 	Scattering asymmetry parameter
| 		*Default: 0.3*
| 		*Type: float*
| 

| **clear_omega**
| 	Single-scattering albedo
| 		*Default: 0.85*
| 		*Type: float*
| 

| **clear_opt_depth**
| 	Elevation of optical depth measurement
| 		*Default: 100.0*
| 		*Type: float*
| 

| **clear_tau**
| 	Optical depth at z
| 		*Default: 0.2*
| 		*Type: float*
| 

| **correct_albedo**
| 	Multiply the solar radiation by 1-snow_albedo.
| 		*Default: true*
| 		*Type: bool*
| 

| **correct_cloud**
| 	Multiply the solar radiation by the cloud factor derived by station data.
| 		*Default: true*
| 		*Type: bool*
| 

| **correct_veg**
| 	Apply solar radiation corrections according to veg_type
| 		*Default: true*
| 		*Type: bool*
| 

| **max**
| 	Maximum possible solar radiation in W/m^2
| 		*Default: 800.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible solar radiation in W/m^2
| 		*Default: 0.0*
| 		*Type: float*
| 


thermal
-------
The thermal section controls all the available parameters that effect the distribution of the thermal module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.thermal`

| **clear_sky_method**
| 	Method for calculating the clear sky thermal radiation
| 		*Default: marks1979*
| 		*Type: string*
| 		*Options:*
 *marks1979 dilley1998 prata1996 angstrom1918*
| 

| **cloud_method**
| 	Method for adjusting thermal radiation due to cloud effects
| 		*Default: garen2005*
| 		*Type: string*
| 		*Options:*
 *garen2005 unsworth1975 kimball1982 crawford1999*
| 

| **correct_cloud**
| 	Specify whether to use the cloud adjustments in thermal calculation
| 		*Default: true*
| 		*Type: bool*
| 

| **correct_terrain**
| 	Specify whether to account for vegetation in the thermal calculations
| 		*Default: true*
| 		*Type: bool*
| 

| **correct_veg**
| 	Specify whether to account for vegetation in the thermal calculations
| 		*Default: true*
| 		*Type: bool*
| 

| **detrend**
| 	Whether to elevationally the detrend prior to distributing
| 		*Default: False*
| 		*Type: bool*
| 

| **detrend_slope**
| 	if detrend is true constrain the detrend_slope to positive (1) or negative (-1) or no constraint (0)
| 		*Default: 0*
| 		*Type: int*
| 		*Options:*
 *-1 0 1*
| 

| **distribution**
| 	Distribution method to use for incoming thermal when using HRRR input data.
| 		*Default: grid*
| 		*Type: string*
| 		*Options:*
 *grid*
| 

| **grid_local**
| 	Use local elevation gradients in gridded interpolation
| 		*Default: False*
| 		*Type: bool*
| 

| **grid_local_n**
| 	number of closest grid cells to use for calculating elevation gradient
| 		*Default: 25*
| 		*Type: int*
| 

| **grid_mask**
| 	Mask the thermal radiation calculations
| 		*Default: True*
| 		*Type: bool*
| 

| **grid_method**
| 	interpolation method to use for this variable
| 		*Default: cubic*
| 		*Type: string*
| 		*Options:*
 *nearest linear cubic*
| 

| **marks1979_nthreads**
| 	Number of threads to use thermal radiation calcs when using Marks1979
| 		*Default: 2*
| 		*Type: int*
| 

| **max**
| 	Maximum possible incoming thermal radiation in W/m^2
| 		*Default: 600.0*
| 		*Type: float*
| 

| **min**
| 	Minimum possible incoming thermal radiation in W/m^2
| 		*Default: 0.0*
| 		*Type: float*
| 


soil_temp
---------
The soil_temp section controls all the available parameters that effect the distribution of the soil_temp module, espcially  the associated models. For more detailed information please see :mod:`smrf.distribute.soil_temp`

| **temp**
| 	Constant value to use for the soil temperature.
| 		*Default: -2.5*
| 		*Type: float*
| 


output
------

| **file_type**
| 	Format to use for outputting data.
| 		*Default: netcdf*
| 		*Type: string*
| 		*Options:*
 *netcdf*
| 

| **frequency**
| 	Number of timesteps between output values. 1 is every timestep.
| 		*Default: 1*
| 		*Type: int*
| 

| **input_backup**
| 	Specify whether to backup the input data and create config file to run the smrf run from that backup
| 		*Default: true*
| 		*Type: bool*
| 

| **mask_output**
| 	Mask the final NetCDF output.
| 		*Default: False*
| 		*Type: bool*
| 

| **out_location**
| 	Directory to output results
| 		*Default: None*
| 		*Type: directory*
| 

| **variables**
| 	Variables to output after being calculated.
| 		*Default: thermal air_temp vapor_pressure wind_speed wind_direction net_solar precip percent_snow snow_density precip_temp*
| 		*Type: string*
| 		*Options:*
 *all air_temp albedo_vis albedo_ir precip percent_snow snow_density storm_days precip_temp clear_ir_beam clear_ir_diffuse clear_vis_beam clear_vis_diffuse cloud_factor cloud_ir_beam cloud_ir_diffuse cloud_vis_beam cloud_vis_diffuse net_solar veg_ir_beam veg_ir_diffuse veg_vis_beam veg_vis_diffuse thermal vapor_pressure dew_point flatwind wind_speed wind_direction thermal_clear thermal_veg thermal_cloud*
| 


system
------

| **log_file**
| 	File path to a txt file for the log info to be outputted
| 		*Default: None*
| 		*Type: filename*
| 

| **log_level**
| 	level of information to be logged
| 		*Default: debug*
| 		*Type: string*
| 		*Options:*
 *debug info error*
| 

| **qotw**
| 	
| 		*Default: false*
| 		*Type: bool*
| 

| **queue_max_values**
| 	How many timesteps that a calculation can get ahead while threading if it is independent of other variables.
| 		*Default: 2*
| 		*Type: int*
| 

| **threading**
| 	Specify whether to use python threading in calculations.
| 		*Default: true*
| 		*Type: bool*
| 

| **time_out**
| 	Amount of time to wait for a thread before timing out
| 		*Default: None*
| 		*Type: float*
| 

