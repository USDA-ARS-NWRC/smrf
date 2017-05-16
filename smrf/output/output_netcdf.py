"""
Functions to output as a netCDF
"""

__version__ = '0.2.2'

import netCDF4 as nc
import numpy as np
from scipy import stats
import logging, os
from datetime import datetime
import pandas as pd

class output_netcdf():
    
    """
    Class output_netcdf() to output values to a netCDF file
    """
    
    type = 'netcdf'
    fmt = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self, variable_list, topo, time, out_frequency):
        """
        Initialize the output_netcdf() class
        
        Args:
            variable_list: list of dicts, one for each variable
            topo: loadTopo instance
        """
        
        self._logger = logging.getLogger(__name__)
        
        # go through the variable list and make full file names
        for v in variable_list:
            variable_list[v]['file_name'] = variable_list[v]['out_location'] + '.nc'
            
        self.variable_list = variable_list
        
        # process the time section
        self.run_time_step = int(time['time_step'])
        self.out_frequency = int(out_frequency)
        
        
        # determine the x,y vectors for the netCDF file
        x = topo.x
        y = topo.y
#         dimensions = ('Time','dateStrLen','y','x')
        dimensions = ('time','y','x')
        self.date_time = {}
    
        for v in self.variable_list:
            
            f = self.variable_list[v]
    
            if os.path.isfile(f['file_name']):
                self._logger.warn('Opening %s, data may be overwritten!' % f['file_name'])
                s = nc.Dataset(f['file_name'], 'a')
#                 h = getattr(s, 'history')
                h = '[%s] Data added or updated' % datetime.now().strftime(self.fmt)
                setattr(s, 'last_modified', h)
                
            else:
                self._logger.debug('Creating %s' % f['file_name'])
                s = nc.Dataset(f['file_name'], 'w', format='NETCDF4', clobber=False)
                            
                # add dimensions
                s.createDimension(dimensions[0], None)
    #             s.createDimension(dimensions[1], 19)
                s.createDimension(dimensions[1], y.shape[0])
                s.createDimension(dimensions[2], x.shape[0])
                
                # create the variables
                s.createVariable('time', 'f', (dimensions[0]))
                s.createVariable('y', 'f', dimensions[1])
                s.createVariable('x', 'f', dimensions[2])
                s.createVariable(f['variable'], 'f', (dimensions[0],dimensions[1],dimensions[2]))
             
                # define some attributes
                setattr(s.variables['time'], 'units', 'hours since %s' % time['start_date'])
                setattr(s.variables['time'], 'calendar', 'standard')
                setattr(s.variables['time'], 'time_zone', time['time_zone'])
                setattr(s.variables['y'], 'units', 'meters')
                setattr(s.variables['y'], 'description', 'UTM, north south')
                setattr(s.variables['x'], 'units', 'meters')
                setattr(s.variables['x'], 'description', 'UTM, east west')
                setattr(s.variables[f['variable']], 'module', f['module'])
                setattr(s.variables[f['variable']], 'units', f['info']['units'])
                setattr(s.variables[f['variable']], 'long_name', f['info']['long_name'])
    
                # define some global attributes
                setattr(s, 'Conventions', 'CF-1.6')
                setattr(s, 'dateCreated', datetime.now().strftime(self.fmt))
                setattr(s, 'title', 'Distirbuted data from SMRF')
                setattr(s, 'history', '[%s] Create netCDF4 file' % datetime.now().strftime(self.fmt))
                
                s.variables['y'][:] = y
                s.variables['x'][:] = x
                
#             self.variable_list[v]['nc_file'] = s
            
            # get all the times from the file if there are any 
#             dt = np.array([''.join(x) for x in s.variables['time'][:]])
#             self.date_time[v] = pd.to_datetime(dt)

#             times = s.variables['time']
#             dates = np.array([])
#             if len(times) != 0:
#                 dates = nc.num2date(times[:],
#                                 units=times.units,
#                                 calendar=times.calendar)
#             self.date_time[v] = dates
                
            s.close()
            
#             # determine the times
#             dt = np.diff(self.date_time[v])/60/1e9
# #             dt = np.array([x.seconds/60 for x in np.diff(self.date_time[v])])   # time difference in minutes
#             dt = dt.astype('float64')
#             if len(dt) > 0:
#                 m = stats.mode(dt)[0][0]    # this is the most likely time steps for the data
#                 
#                 if self.out_frequency*self.run_time_step % m != 0:
#                     raise Exception('netCDF file has a different output frequency than desired, please check or move file %s' % f['file_name'])
                
            
    
    def output(self, variable, data, date_time):
        """
        Output a time step
        
        Args:
            variable: variable name that will index into variable list
            data: the variable data
            date_time: the date time object for the time step
        """
        
        self._logger.debug('%s Writing variable %s to netCDF' % (date_time, variable))
        
#         f = self.variable_list[variable]['nc_file']
        f = nc.Dataset(self.variable_list[variable]['file_name'], 'a', 'NETCDF4')
        
        # the current time integer
        times = f.variables['time']
        t = nc.date2num(date_time.replace(tzinfo=None), times.units, times.calendar)
        
        if len(times) != 0:
            index = np.where(times[:] == t)[0]
            if index.size == 0:
                index = len(times)
            else:
                index = index[0]
        else:
            index = len(times)
            
#         self.date_time[variable] = np.append(self.date_time[variable], pd.to_datetime(date_time))
            
            # insert the time
        f.variables['time'][index] = t
            
        # insert the data
        f.variables[variable][index,:] = data
        
        # synce the data to disk to that it can be viewed immediately
#         f.sync()
        f.close()
        
        
        
        
        
        
        
