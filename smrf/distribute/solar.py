"""
20160106 Scott Havens

Distribute solar radiation

"""

import numpy as np
import logging, os
import subprocess as sp
from smrf.distribute import image_data
from smrf.envphys import radiation
import smrf.utils as utils
from smrf import ipw

# import smrf.utils as utils
# import matplotlib.pyplot as plt

class solar(image_data.image_data):
    """
    ta extends the base class of image_data()
    The solar() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        config: configuration from [solar] section
        solar_vis: numpy matrix of the visible solar
        solar_ir: numpy matrix of the ir solar
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'solar'
    min = 0
    max = 1200
    
    def __init__(self, solarConfig, albedoConfig, stoporad_in, tempDir=None):
        """
        Initialize solar()
        
        Args:
            solarConfig: configuration from [solar] section
            albedoConfig: configuration from [albedo] section
            stoporad_in: file path to the stoporad_in file created from topo()
            tempDir: location of temp/working directory
        """
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration        
        if 'clear_opt_depth' not in solarConfig:
            solarConfig['clear_opt_depth'] = 100
        else:
            solarConfig['clear_opt_depth'] = float(solarConfig['clear_opt_depth'])
        
        if 'clear_tau' not in solarConfig:
            solarConfig['clear_tau'] = 0.2
        else:
            solarConfig['clear_tau'] = float(solarConfig['clear_tau'])
            
        if 'clear_omega' not in solarConfig:
            solarConfig['clear_omega'] = 0.85
        else:
            solarConfig['clear_omega'] = float(solarConfig['clear_omega'])
        
        if 'clear_gamma' not in solarConfig:
            solarConfig['clear_gamma'] = 0.3
        else:
            solarConfig['clear_gamma'] = float(solarConfig['clear_gamma'])
        
        self.getConfig(solarConfig)
        self.albedoConfig = albedoConfig
        
        self.stoporad_in = stoporad_in
                
        if (tempDir is None) | (tempDir == 'TMPDIR'):
            tempDir = os.environ['TMPDIR']
        self.tempDir = tempDir        
        
        # stoporad file names
        self.ir_file = os.path.join(self.tempDir, 'clearsky_ir.ipw')
        self.vis_file = os.path.join(self.tempDir, 'clearsky_vis.ipw')
        
                
        self._logger.debug('Initialized distribute.solar')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
            
        """
        
        self._initialize(topo, metadata)
                  
            
        
    def distribute(self, data, illum_ang, cosz, azimuth, min_storm_day, albedo_vis, albedo_ir):
        """
        Distribute solar
        
        Args:
            data: cloud_factor data frame
            cosz: cosine of the zenith angle for the basin
            azimuth: azimuth to the sun for the basin 
            min_storm_day: decimal day of last storm for the entire basin
            
            
        """
    
        self._logger.debug('Distributing solar')
        
        # only need to calculate solar if the sun is up
        if cosz > 0:
               
            #------------------------------------------------------------------------------ 
            # calculate clear sky radiation
                    
            # get the current day of water year
            wy_day, wyear = utils.water_day(data.name)
            
            # determine the minutes west of timezone
            tz_min_west = np.abs(data.name.utcoffset().total_seconds()/60)
                
            # Calculate ir radiation
            self._logger.debug('Calculating clear sky radiation, ir')
            
            ir_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.7,2.8 -s %s'\
                ' -d %s -f %i -y %i -A %s,%s -a %i -m %i -c %i -D %s > %s' \
                % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
                   str(self.config['clear_omega']), str(self.config['clear_gamma']), \
                   str(min_storm_day), str(wy_day), tz_min_west, wyear, \
                   str(cosz), str(azimuth), self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
                   self.albedoConfig['dirt'], self.stoporad_in, self.ir_file)
            irp = sp.Popen(ir_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']}).wait()
            
            if irp != 0:
                raise Exception('Clear sky for IR failed')
                        
            # Calculate visible radiation
            self._logger.debug('Calculating clear sky radiation, visible')
            
            vis_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.28,0.7 -s %s'\
                ' -d %s -f %i -y %i -A %s,%s -a %i -m %i -c %i  -D %s > %s' \
                % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
                   str(self.config['clear_omega']), str(self.config['clear_gamma']), \
                   str(min_storm_day), str(wy_day), tz_min_west, wyear, \
                   str(cosz), str(azimuth), self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
                   self.albedoConfig['dirt'], self.stoporad_in, self.vis_file)
            visp = sp.Popen(vis_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']}).wait()   

            if visp != 0:
                raise Exception('Clear sky for visible failed')

            # load clear sky files back in
            vis = ipw.IPW(self.vis_file)
            self.clear_vis_beam = vis.bands[0].data
            self.clear_vis_diffuse = vis.bands[1].data
            
            ir = ipw.IPW(self.ir_file)
            self.clear_ir_beam = ir.bands[0].data
            self.clear_ir_diffuse = ir.bands[1].data
            
            #------------------------------------------------------------------------------ 
            # correct clear sky for cloud


    
        else:
            
            self._logger.debug('Sun is down, goodnight')
            
            self.clear_vis = np.zeros(albedo_vis.shape)
            self.clear_ir = np.zeros(albedo_vis.shape)
            
            
            
            
            
            
            
            
            
    
    