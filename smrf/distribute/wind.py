"""
20160104 Scott Havens

Distribute wind_speed and wind_direction

"""

import numpy as np
import logging, os
from smrf.distribute import image_data
import smrf.utils as utils
import netCDF4 as nc
import matplotlib.pyplot as plt

class wind(image_data.image_data):
    """
    ta extends the base class of image_data()
    The wind() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        config: configuration from [vapor_pressure] section
        wind_speed: numpy matrix of the wind speed
        wind_direction: numpy matrix of the wind direction
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'wind'
    min = 0.447
    max = 35
    
    def __init__(self, windConfig, tempDir=None):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration
        self.getConfig(windConfig)
        
        if (tempDir is None) | (tempDir == 'TMPDIR'):
            tempDir = os.environ['TMPDIR']
        self.tempDir = tempDir
        
        # open the maxus netCDF
        self._maxus_file = nc.Dataset(self.config['maxus_netcdf'], 'r')
        self.maxus = self._maxus_file.variables['maxus']
        self._logger.debug('Opened %s' % self._maxus_file)
        
        # check maxus defaults
        if 'station_default' not in self.config:
            self.config['station_default'] = 11.4
        if 'veg_default' not in self.config:
            self.config['veg_default'] = 11.4
            
        # get the veg values
        matching = [s for s in self.config.keys() if "veg_" in s]
        v = {}
        for m in matching:
            if m != 'veg_default':
                ms = m.split('_')
                v[ms[1]] = float(self.config[m])
        self.config['veg'] = v

        # peak value
        if 'peak' in self.config:
            self.config['peak'] = self.config['peak'].split(',')
        else:
            self.config['peak'] = None
        
        self._logger.debug('Initialized distribute.wind')     
        
        
        
    def __del__(self):
        self._maxus_file.close()
        self._logger.debug('Closed %s' % self._maxus_file)
        
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
                        
        """
        
        self._initialize(topo, metadata)
        
        self.veg_type = topo.veg_type.bands[0].data
        
        # get the enhancements for the stations
        if 'enhancement' not in self.metadata.columns:
            self.metadata['enhancement'] = float(self.config['station_default'])
            
            for m in self.metadata.index:
                if m.lower() in self.config:
                    self.metadata.loc[m, 'enhancement'] = float(self.config[m.lower()])
        
    def distribute(self, data_speed, data_direction):
        """
        Distribute wind
        
        Args:
            data_speed: wind_speed data frame for single time step
            data_direction: wind_direction data frame for single time step
            
        Returns:
            self.wind_speed: wind_speed matrix
            self.wind_direction: wind_direction matrix, corrected if dpt > ta 
        """
        
        self._logger.debug('Distributing wind_direction')
    
        data_speed = data_speed[self.stations]
        data_direction = data_direction[self.stations]
        
        # calculate the maxus at each site
        self.stationMaxus(data_speed, data_direction)
        
        # distribute the flatwind
        self._distribute(self.flatwind, other_attribute='flatwind_distributed')
        
        # distribute u_direction and v_direction
        self._distribute(self.u_direction, other_attribute='u_direction_distributed')
        self._distribute(self.v_direction, other_attribute='v_direction_distributed')
        
        # Calculate simulated wind speed at each cell from flatwind
        self.simulateWind(data_speed)
        
    
    def simulateWind(self, data_speed):
        """
        Calculate the simulated wind speed at each cell from flatwind
        and the distributed directions
        
        Args:
            data_speed: wind_speed dataframe to make the pixel locations same as the
                measured values
        """
        
        # combine u and v to azimuth
        az = np.arctan2(self.u_direction_distributed, self.v_direction_distributed)*180/np.pi
        az[az < 0] = az[az < 0] + 360 
    
        
        dir_round_cell = np.ceil((az - self.nstep/2) / self.nstep) * self.nstep
        dir_round_cell[dir_round_cell < 0] = dir_round_cell[dir_round_cell < 0] + 360
        dir_round_cell[dir_round_cell == -0] = 0
        dir_round_cell[dir_round_cell == 360] = 0
        
        cellmaxus = np.zeros(dir_round_cell.shape)
        cellwind = np.zeros(dir_round_cell.shape)
                    
        dir_unique = np.unique(dir_round_cell)
        for d in dir_unique:
            # find all values for matching direction
            ind = dir_round_cell == d
            i = np.argwhere(self._maxus_file.variables['direction'][:] == d)[0][0]
            cellmaxus[ind] = self.maxus[i][ind]
            
        # correct for veg
        for i,v in enumerate(self.config['veg']):
            cellmaxus[self.veg_type == int(v)] += self.config['veg'][v]
                    
        # correct unreasonable values
        cellmaxus[cellmaxus > 32] = 32
        cellmaxus[cellmaxus < -32] = -32
            
        # determine wind
        factor = float(self.config['reduction_factor'])
        ind = cellmaxus < -30.10
        cellwind[ind] = factor * self.flatwind_distributed[ind] * 4.211
        
        ind = (cellmaxus > -30.10) & (cellmaxus < -21.3)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind_distributed[ind] * (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c,2) - 0.0003651592 * np.power(c, 3))
        
        ind = (cellmaxus > -21.3) & (cellmaxus < 0)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind_distributed[ind] * (1.0 + 0.1031717 * c - 0.008003561 * np.power(c,2) + 0.0003996581 * np.power(c,3))
        
        ind = cellmaxus > 30.10
        cellwind[ind] = self.flatwind_distributed[ind] / 4.211
        
        ind = (cellmaxus < 30.10) & (cellmaxus > 21.3)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind_distributed[ind] / (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c,2) - 0.0003651592 * np.power(c,3))
        
        ind = (cellmaxus < 21.3) & (cellmaxus >= 0)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind_distributed[ind] / (1.0 + 0.1031717 * c - 0.008003561 * np.power(c,2) + 0.0003996581 * np.power(c,3))     
        
        
        # Convert from 3m to 5m wind speed
        cellwind *= 1.07985;
        
        # preseve the measured values
        cellwind[self.metadata.xi, self.metadata.xi] = data_speed
        
        # check for NaN
        nans, x = utils.nan_helper(cellwind)
    
        if np.sum(nans) > 0:
            cellwind[nans] = np.interp(x(nans), x(~nans), cellwind[~nans])
    
        self.wind_speed = utils.set_min_max(cellwind, self.min, self.max)
        self.wind_direction = az
    
       
    
    def stationMaxus(self, data_speed, data_direction):
        """
        Determine the maxus value at the station given the wind direction.
        Can specify the enhancemet for each station or use the default, along
        with whether or not the staiton is on a peak which will ensure that 
        the station cannot be sheltered        
        
        Args:
            data_speed: wind_speed data frame for single time step
            data_direction: wind_direction data frame for single time step
            
        Returns:
            self.flatwind: data_speed values converted to flatwind values dataframe
            self.u_direction: u componenets of wind_direction in dataframe
            self.v_direction: v componenets of wind_direction in dataframe    
            
        """
        
        #------------------------------------------------------------------------------ 
        # Get data and site maxus value
        flatwind = data_speed.copy()
        
        # number of bins that the maxus library was calculated for
        self.nbins = len(self._maxus_file.dimensions['Direction'])
        self.nstep = 360/self.nbins
        
        for m in self.metadata.index:
            
            # pixel locations
            xi = self.metadata.loc[m, 'xi']
            yi = self.metadata.loc[m, 'yi']
            e = self.metadata.loc[m,'enhancement']
                                    
            # maxus value at the station
            if not np.isnan(data_direction[m]):
                                
                if m in self.config['peak']:
                    val_maxus = np.min(self.maxus[:, yi, xi] + e)
                
                else:
                    idx = int(np.ceil((data_direction[m] - self.nstep/2) / self.nstep) * self.nstep)
                    ind = self._maxus_file.variables['direction'][:] == idx
                    
                    val_maxus = self.maxus[ind, yi, xi] + e
                
                
                # correct unreasonable values
                if val_maxus > 35: val_maxus = 35
                if val_maxus < -35: val_maxus = -35
                
                ma = np.abs(val_maxus)
               
                # Lapse all measurements to flat terrain (i.e. maxus = 0)     
                if (ma > 21.3 and ma < 30.0):
                    expVal = 1.756507 - 0.1678945 * ma + 0.01927844 * np.power(ma,2) - 0.0003651592 * np.power(ma,3)
                elif (ma >= 30.0):
                    expVal = 4.21
                else:
                    expVal = 1.0 + 0.1031717 * (ma) - 0.008003561 * np.power(ma,2) + 0.0003996581 * np.power(ma,3)
                    
                if val_maxus > 0:
                    flatwind.loc[m] = data_speed[m] * expVal
                else:
                    flatwind.loc[m] = data_speed[m] / expVal
            else:
                flatwind.loc[m] = np.NaN
        
        
        self.flatwind = flatwind
        
        # wind direction components at the station
        self.u_direction = np.sin(data_direction * np.pi/180)    # u
        self.v_direction = np.cos(data_direction * np.pi/180)    # v
    
    

def cellMaxus(cellmaxus, flatwind, factor):
    """
    Apply the equations for the cell maxus
    """   
    
    if cellmaxus < -30.10:
        cellwind = factor * flatwind * 4.211
    elif (cellmaxus > -30.10) & (cellmaxus < -21.3):
        cellwind = factor * flatwind * (1.756507 - 0.1678945 * np.abs(cellmaxus) + 0.01927844 * np.power(np.abs(cellmaxus),2) - 0.0003651592 * np.power(np.abs(cellmaxus), 3))
    elif (cellmaxus > -21.3) & (cellmaxus < 0):
        cellwind = factor * flatwind * (1.0 + 0.1031717 * np.abs(cellmaxus) - 0.008003561 * np.power(np.abs(cellmaxus),2) + 0.0003996581 * np.power(np.abs(cellmaxus),3))
    elif cellmaxus > 30.10:
        cellwind = flatwind / 4.211
    elif (cellmaxus < 30.10) & (cellmaxus > 21.3):
        cellwind = flatwind / (1.756507 - 0.1678945 * (cellmaxus) + 0.01927844 * np.power(cellmaxus,2) - 0.0003651592 * np.power(cellmaxus,3))
    elif (cellmaxus < 21.3) & (cellmaxus >= 0):
        cellwind = flatwind / (1.0 + (0.1031717 * cellmaxus) - (0.008003561 * np.power(cellmaxus,2)) + (0.0003996581 * np.power(cellmaxus,3)))
        
    return cellwind
        
        
        
        
    
    