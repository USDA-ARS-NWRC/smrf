"""
Functions to output as a netCDF
"""

import netCDF4 as nc
import logging, os
from datetime import datetime

class output_netcdf():
    
    """
    Class output_netcdf() to output values to a netCDF file
    """
    
    type = 'netcdf'
    
    def __init__(self, variable_list, topo):
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
        
        # determine the x,y vectors for the netCDF file
        x = topo.x
        y = topo.y
        dimensions = ('Time','dateStrLen','y','x')
    
        for v in self.variable_list:
            
            f = self.variable_list[v]
    
            if os.path.exists(f['file_name']):
                self._logger.debug('Opening %s' % f['file_name'])
                s = nc.Dataset(f['file_name'], 'r+', 'NETCDF4')

            else:
                self._logger.debug('Creating %s' % f['file_name'])
                s = nc.Dataset(f['file_name'], 'w', 'NETCDF4')
                                
                # add dimensions
                s.createDimension(dimensions[0], None)
                s.createDimension(dimensions[1], 19)
                s.createDimension(dimensions[2], y.shape[0])
                s.createDimension(dimensions[3], x.shape[0])
                
                # create the variables
                s.createVariable('Times', 'c', (dimensions[0],dimensions[1]))
                s.createVariable('y', 'f', dimensions[2])
                s.createVariable('x', 'f', dimensions[3])
                s.createVariable(f['variable'], 'f', (dimensions[0],dimensions[2],dimensions[3]))
             
                # define some attributes
                setattr(s.variables['y'], 'units', 'meters')
                setattr(s.variables['y'], 'description', 'UTM, north south')
                setattr(s.variables['x'], 'units', 'meters')
                setattr(s.variables['x'], 'description', 'UTM, east west')
                setattr(s.variables[f['variable']], 'module', f['module'])
    #             setattr(s.variables['rad'], 'units', 'W/m2')
    #             setattr(s.variables['rad'], 'description', 'Net solar radiation')
                setattr(s, 'dateCreated', datetime.now().isoformat())
             
                s.variables['y'][:] = y
                s.variables['x'][:] = x
                
            self.variable_list[v]['nc_file'] = s
            
            
    
    def output(self, variable, data, date_time):
        """
        Output a time step
        
        Args:
            variable: variable name that will index into variable list
            data: the variable data
            date_time: the date time object for the time step
        """
        
        self._logger.debug('Writing variable %s to netCDF' % variable)
        
        f = self.variable_list[variable]['nc_file']
        
        # determine what inde to put into netCDF, len() will give the end of the values
        # check if there is a time there already
        index = len(f.dimensions['Time'])
        
        # insert the time
        f.variables['Times'][index,:] = date_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # insert the data
        f.variables[variable][index,:] = data
        
        # synce the data to disk to that it can be viewed immediately
        f.sync()
        
        
        
        
        
        
        
