__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-01"
__version__ = "0.2.1"


import numpy as np
import logging, os
from smrf.distribute import image_data
from smrf.utils import utils
from smrf import envphys
from smrf.envphys.core import envphys_c
# import matplotlib.pyplot as plt

class vp(image_data.image_data):
    """
    The :mod:`~smrf.distribute.vapor_pressure.vp` class allows for variable specific distributions that 
    go beyond the base class
    
    Vapor pressure is provided as an argument and is calcualted from coincident air temperature and
    relative humidity measurements using utilities such as IPW's ``rh2vp``. The vapor pressure is distributed
    instead of the relative humidity as it is an absolute measurement of the vapor within the atmosphere 
    and will follow elevational trends (typically negative).  Were as relative humidity is a relative measurement which varies
    in complex ways over the topography.  From the distributed vapor pressure, the dew point is
    calculated for use by other distribution methods. The dew point temperature is further corrected to
    ensure that it does not exceed the distributed air temperature.
    
    Args:
        vpConfig: The [vapor_pressure] section of the configuration file
    
    Attributes:
        config: configuration from [vapor_pressure] section
        vapor_pressure: numpy matrix of the vapor pressure
        dew_point: numpy matrix of the dew point, calculated from vapor_pressure
            and corrected for dew_point greater than air_temp
        min: minimum value of vapor pressure is 10 Pa
        max: maximum value of vapor pressure is 7500 Pa
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.vapor_pressure.vp`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'vapor_pressure'
    
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
    
    def __init__(self, vpConfig):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration
        self.getConfig(vpConfig)
        
        if 'nthreads' not in self.config:
            self.config['nthreads'] = '1'
                
        self._logger.debug('Created distribute.vapor_pressure')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls :mod:`smrf.distribute.image_data.image_data._initialize`.
        Preallocates the following class attributes to zeros:
        
        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`    
                        
        """
        
        self._logger.debug('Initializing distribute.vapor_pressure')
        self._initialize(topo, metadata)
        
        

    def distribute(self, data, ta):
        """
        Distribute air temperature given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.
        
        The following steps are performed when distributing vapor pressure:
        
        1. Distribute the point vapor pressure measurements
        2. Calculate dew point temperature using :mod:`smrf.envphys.core.envphys_c.cdewpt`
        3. Adjsut dew point values to not exceed the air temperature
        
        Args:
            data: Pandas dataframe for a single time step from precip
            ta: air temperature numpy array that will be used for calculating dew point temperature
            
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
        envphys_c.cdewpt(self.vapor_pressure, dpt, 
                      float(self.config['tolerance']), 
                      int(self.config['nthreads']))
                
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
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and call :mod:`smrf.distribute.vapor_pressure.vp.distribute` then
        puts the distributed data into the queue for:
        
        * :py:attr:`vapor_pressure`
        * :py:attr:`dew_point`
         
        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        
        for t in data.index:
            
            ta = queue['air_temp'].get(t)
            
            self.distribute(data.ix[t], ta)
        
            queue[self.variable].put( [t, self.vapor_pressure] )
            queue['dew_point'].put( [t, self.dew_point] )

    
    
    
