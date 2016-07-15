"""
20160104 Scott Havens

Distribute vapor pressure

"""

import numpy as np
import logging, os
from smrf.distribute import image_data
from smrf.utils import utils
# from smrf.envphys.core import core_c
# import matplotlib.pyplot as plt

class vp(image_data.image_data):
    """
    ta extends the base class of image_data()
    The vp() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        config: configuration from [vapor_pressure] section
        vapor_pressure: numpy matrix of the vapor pressure
        dew_point: numpy matrix of the dew point, calculated from vapor_pressure
            and corrected for dew_point > air_temp
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'vapor_pressure'
    min = 10
    max = 7500
    
    # these are variables that can be output
    output_variables = {'vapor_pressure':{
                                  'units': 'Pa',
                                  'long_name': 'vapor_pressure'
                                  },
                         'dew_point':{
                                  'units': 'degree Celcius',
                                  'long_name': 'dew_point_temperature'
                                  }
                        }
    
    def __init__(self, vpConfig, tempDir=None):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration
        self.getConfig(vpConfig)
        
        if 'nthreads' not in self.config:
            self.config['nthreads'] = '1'
        
        
        if (tempDir is None) | (tempDir == 'TMPDIR'):
            tempDir = os.environ['TMPDIR']
        self.tempDir = tempDir
        
        self._logger.debug('Created distribute.vapor_pressure')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
                        
        """
        
        self._logger.debug('Initializing distribute.vapor_pressure')
        self._initialize(topo, metadata)
        
        

    def distribute(self, data, ta):
        """
        Distribute air temperature
        
        Args:
            data: vapor_pressure data frame for single time step
            ta: ta.air_temp matrix to ensure dpt is below air temp
            
        Returns:
            self.vapor_pressure: vp matrix
            self.dew_point: dew point matrix, corrected if dpt > ta 
        """
        
        self._logger.debug('%s -- Distributing vapor_pressure' % data.name)
    
        # calculate the vapor pressure
        self._distribute(data)
        
        # set the limits
        self.vapor_pressure = utils.set_min_max(self.vapor_pressure, self.min, self.max)
        
        # calculate the dew point
        self._logger.debug('%s -- Calculating dew point' % data.name)
        
#         # make a vapor pressure IPW file
#         vpfile = os.path.join(self.tempDir, 'vp%04i.ipw' % randint(0,9999))
#         i = ipw.IPW()
#         i.new_band(self.vapor_pressure)
#         i.write(vpfile, nbits=16)
#         
#         # calculate the dew point
#         dptfile = os.path.join(self.tempDir, 'dpt%04i.ipw' % randint(0,9999))
#         dp_cmd = 'idewptp -t %s -P %s %s > %s' % (self.config['tolerance'], str(self.config['nthreads']), vpfile, dptfile)
# #         p = sp.Popen(dp_cmd, shell=True).wait()
#         
#         p = sp.Popen(dp_cmd, shell=True)
#         stdoutdata, stderrdata = p.communicate()
#             
#         self._logger.debug(stdoutdata)
#         self._logger.debug(stderrdata)
#             
#         if p.returncode != 0:
#             raise OSError('idewpt failure')
#         
#         # read in the dew point file
#         dp = ipw.IPW(dptfile)
#         dpt = dp.bands[0].data.astype(np.float64)
              
        # use the core_c to calculate the dew point
        dpt = np.zeros_like(self.vapor_pressure, dtype=np.float64)
#         core_c.cdewpt(self.vapor_pressure, dpt, 
#                       float(self.config['tolerance']), 
#                       int(self.config['nthreads']))
                
        # find where dpt > ta
        ind = dpt >= ta
        
        if (np.sum(ind) > 0):# or np.sum(indm) > 0):
            dpt[ind] = ta[ind] - 0.2
            
        self.dew_point = dpt
        
        # clean up
#         os.remove(dptfile)
#         os.remove(vpfile)
        
        
    
    def distribute_thread(self, queue, data):
        """
        Distribute the data using threading and queue
        
        Args:
            queue: queue dict for all variables
            data: pandas dataframe for all data required
        
        Output:
            Changes the queue air_temp for the given date
        """
        
        for t in data.index:
            
            ta = queue['air_temp'].get(t)
            
            self.distribute(data.ix[t], ta)
        
            queue[self.variable].put( [t, self.vapor_pressure] )
            queue['dew_point'].put( [t, self.dew_point] )

    
    
    