

Distribution Methods
====================

Comming soon!

Detrending Measurement Data
```````````````````````````

Most meterological variables used in SMRF have an underlying elevational gradient.  Therefore,
all of the distribution methods can estimate the gradient from the measurement data and apply
the elevational gradient to the DEM during distribution. Here, the theory of how the elevational
gradient is calcualted, removed from the data, and reapplied after distirbution is explained. All
the distribution methods follow this pattern.

Calculating the Elevational Trend
   
   The elevational trend for meterological stations is calculated using all available stations
   in the modeling domain.
   
   Gridded datasets have significantly more information than point measurements. Therefore, the
   approach is slightly different for calculating the elevational trend.  To limit the number of
   grid cells that contribute to the elevational trend, only those grid cells within the mask are
   used.  This ensures 






Methods
```````

Inverse Distance Weighting
--------------------------

Detrended Kriging
-----------------

Gridded Interpolation
---------------------
