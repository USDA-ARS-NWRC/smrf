'''
Version = 0.1.1
20160307 Scott Havens
'''

# from smrf import ipw
import numpy as np
import netCDF4 as nc
import pandas as pd
import logging
import os
import utm
import subprocess as sp

# import matplotlib.pyplot as plt

class grid():
    '''
    Class for loading and storing the data, either from 
    a gridded dataset in:
    - NetCDF format
    - other format
        
    Inputs to data() are:
    - dataConfig, from the [gridded] section
    - start_date, datetime object
    - end_date, datetime object
        
    '''
    
    def __init__(self, dataConfig, topo, start_date, end_date, time_zone='UTC', dataType='wrf', tempDir=None):
                
                
        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']
            
        self.tempDir = tempDir
        self.dataConfig = dataConfig
        self.dataType = dataType
        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = time_zone
        
        # The data that will be output
        self.variables = ['air_temp', 'vapor_pressure', 'precip', 'wind_speed', 'wind_direction', 'cloud_factor', 'thermal']
        
        # get the bounds of the model so that only the values inside the model domain are used
        self.x = topo.x
        self.y = topo.y
        
        
        
        self._logger = logging.getLogger(__name__)


        # load the data        
        if dataType == 'wrf':
            self.load_from_wrf()
        elif dataType == 'netcdf':
            self.load_from_netcdf()
        else:
            raise Exception('Could not resolve dataType')
        
#         # correct for the timezone
#         for v in self.variables:
#             d = getattr(self, v)
#             setattr(self, v, d.tz_localize(tz=self.time_zone))
        
    
    def load_from_netcdf(self):
        '''
        Load the data from a generic netcdf file
        
        Args:
            lat: latitude field in file, 1D array
            lon: longitude field in file, 1D array
            elev: elevation field in file, 2D array
            variable: variable name in file, 3D array
        '''
        
        self._logger.info('Reading data coming from netcdf: {}'.format(self.dataConfig['file']))
        
        f = nc.Dataset(self.dataConfig['file'], 'r')
        
        
        ### GET THE LAT, LON, ELEV FROM THE FILE ###
        mlat = f.variables['lat'][:]
        mlon = f.variables['lon'][:]
        mhgt = f.variables['elev'][:]
        
        [mlon, mlat] = np.meshgrid(mlon, mlat)
        
        ### GET THE METADATA ###
        # create some fake station names based on the index
        a = np.argwhere(mlon)
        primary_id = ['grid_y%i_x%i' % (i[0], i[1]) for i in a]
        self._logger.debug('{} grid cells within model domain'.format(len(a)))
        
        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=primary_id,
                                columns=('X','Y','latitude','longitude','elevation'))
        
        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm, axis=1)
        
        self.metadata = metadata    
     
    def load_from_wrf(self):
        '''
        Load the data from a netcdf file. This was setup to work with a WRF output file,
        i.e. wrf_out so it's going to look for the following variables:
        - Times
        - XLAT
        - XLONG
        - HGT
        - T2
        - DWPT
        - GLW
        - RAINNC
        - CLDFRA
        - UGRD
        - VGRD
        
        Each cell will be identified by grid_IX_IY
        
        '''
        
        self.wrf_variables = ['GLW','T2','DWPT','UGRD','VGRD','CLDFRA','RAINNC']
#         self.variables = ['thermal','air_temp','dew_point','wind_speed','wind_direction','cloud_factor','precip']
        
        # degree offset for a buffer around the model domain
        offset = 0.1
        
        self._logger.info('Reading data coming from WRF output: {}'.format(self.dataConfig['file']))
        f = nc.Dataset(self.dataConfig['file'])
        
        
        ### DETERMINE THE MODEL DOMAIN AREA IN THE GRID ###
        dlat = np.zeros((2,))
        dlon = np.zeros_like(dlat)
        dlat[0], dlon[0] = utm.to_latlon(np.min(self.x), np.min(self.y), 
                                         int(self.dataConfig['zone_number']),
                                         self.dataConfig['zone_letter'])
        dlat[1], dlon[1] = utm.to_latlon(np.max(self.x), np.max(self.y), 
                                         int(self.dataConfig['zone_number']),
                                         self.dataConfig['zone_letter'])
        # add a buffer
        dlat[0] -= offset
        dlat[1] += offset
        dlon[0] -= offset
        dlon[1] += offset
        
        # get the values that are in the modeling domain
        ind = (f.variables['XLAT'] >= dlat[0]) & \
            (f.variables['XLAT'] <= dlat[1]) & \
            (f.variables['XLONG'] >= dlon[0]) & \
            (f.variables['XLONG'] <= dlon[1])
            
        
        mlat = f.variables['XLAT'][:][ind]
        mlon = f.variables['XLONG'][:][ind]
        mhgt = f.variables['HGT'][:][ind]
        
        
        ### GET THE METADATA ###
        # create some fake station names based on the index
        a = np.argwhere(ind)
        primary_id = ['grid_y%i_x%i' % (i[0], i[1]) for i in a]
        self._logger.debug('{} grid cells within model domain'.format(len(a)))
        
        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=primary_id,
                                columns=('X','Y','latitude','longitude','elevation'))
        
        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm, axis=1)
            
        self.metadata = metadata
        
        
        ### GET THE TIMES ###
        t = f.variables['Times']
        t.set_auto_maskandscale(False)
        times = [('').join(v) for v in t]
        times = [v.replace('_', ' ') for v in times]  # remove the underscore
        time = pd.to_datetime(times)
        
        # subset the times to only those needed
        time_ind = (time >= pd.to_datetime(self.start_date)) & (time <= pd.to_datetime(self.end_date))
        time = time[time_ind]
                
                
        ### GET THE DATA, ONE AT A TIME ###
        self._logger.debug('Loading air_temp')
        self.air_temp = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['T2'][time_ind, i[0], i[1]] - 273.15
            self.air_temp[g] = v
            
        
        self._logger.debug('Loading dew_point and calculating vapor_pressure')
        self.vapor_pressure = pd.DataFrame(index=time, columns=primary_id)
        self.dew_point = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['DWPT'][time_ind, i[0], i[1]]
            self.dew_point[g] = v
            
            tmp_file = os.path.join(self.tempDir, 'dpt.txt')        
            np.savetxt(tmp_file, v)   
            
            dp_cmd = 'satvp < %s' % tmp_file
            p = sp.Popen(dp_cmd, shell=True, stdout=sp.PIPE)
            out, err = p.communicate()
            
            x = np.array(filter(None, out.split('\n')), dtype='|S8')
            y = x.astype(np.float64)
            
            self.vapor_pressure[g] = y
        sp.Popen('rm %s' % tmp_file, shell=True)
        
        
        self._logger.debug('Loading thermal')
        self.thermal = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['GLW'][time_ind, i[0], i[1]]
            self.thermal[g] = v
            
        
        self._logger.debug('Loading cloud_factor')
        self.cloud_factor = pd.DataFrame(index=time, columns=primary_id)
        cf = 1 - np.mean(f.variables['CLDFRA'][time_ind, :], axis=1)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = cf[:, i[0], i[1]]
            self.cloud_factor[g] = v
        
        
        self._logger.debug('Loading wind_speed and wind_direction')
        self.wind_speed = pd.DataFrame(index=time, columns=primary_id)
        self.wind_direction = pd.DataFrame(index=time, columns=primary_id)
        min_speed = 0.47
        
        u10 = f.variables['UGRD'][time_ind, :]
        v10 = f.variables['VGRD'][time_ind, :]
        
        # calculate the wind speed
        s = np.sqrt(u10**2 + v10**2)
        s[s < min_speed] = min_speed
        
        # calculate the wind direction
        d = np.degrees(np.arctan2(v10,u10))
        
        ind = d < 0
        d[ind] = d[ind] + 360
        
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            
            self.wind_speed[g] = s[:, i[0], i[1]]
            self.wind_direction[g] = d[:, i[0], i[1]]
            
        
        self._logger.debug('Loading precip')
        self.precip = pd.DataFrame(index=time, columns=primary_id)
        precip = np.diff(f.variables['RAINNC'][time_ind, :], axis=0)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            self.precip[g] = np.concatenate(([0], precip[:, i[0], i[1]]))
        
        # correct for the timezone and get only the desired dates
        for v in self.variables:
            d = getattr(self, v)
            # d = d[self.start_date : self.end_date] # step performed above while reading in the data
            setattr(self, v, d.tz_localize(tz=self.time_zone))
            
        
                            
def apply_utm(s):
    """
    Calculate the utm from lat/lon for a series
    
    Args:
        s: pandas series with fields latitude and longitude
        
    Returns:
        s: pandas series with fields 'X' and 'Y' filled
    """
    p = utm.from_latlon(s.latitude, s.longitude)
    s['X'] = p[0]
    s['Y'] = p[1]
    return s
            
           
        
        
        
        
