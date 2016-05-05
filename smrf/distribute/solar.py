"""
20160106 Scott Havens

Distribute solar radiation

"""

import numpy as np
import logging, os
import subprocess as sp
from multiprocessing import Process
from smrf.distribute import image_data
from smrf.envphys import radiation
from smrf.utils import utils
from smrf import ipw

# import matplotlib.pyplot as plt

class solar(image_data.image_data):
    """
    ta extends the base class of image_data()
    The solar() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        albedoConfig
        clear_ir_beam
        clear_ir_diffuse
        clear_vis_beam
        clear_vis_diffuse
        cloud_factor
        cloud_ir_beam
        cloud_ir_diffuse
        cloud_vis_beam
        cloud_vis_diffuse
        config
        idw
        ir_file
        metadata
        net_solar
        solar
        stations
        stoporad_in
        tempDir
        variable
        veg_height
        veg_ir_beam
        veg_ir_diffuse
        veg_k
        veg_tau
        veg_vis_beam
        veg_vis_diffuse
        vis_file
    
    """
    
    variable = 'solar'
    min = 0
    max = 1200
    
    # these are variables that can be output
    output_variables = {'clear_ir_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'clear_sky_infrared_beam'
                                  },
                        'clear_ir_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'clear_sky_infrared_diffuse'
                                  },
                        'clear_vis_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'clear_sky_visible_beam'
                                  },
                        'clear_vis_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'clear_sky_visible_diffuse'
                                  },
                        'cloud_factor':{
                                  'units': 'None',
                                  'long_name': 'cloud_factor'
                                  },
                        'cloud_ir_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'cloud_infrared_beam'
                                  },
                        'cloud_ir_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'cloud_infrared_diffuse'
                                  },
                        'cloud_vis_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'cloud_visible_beam'
                                  },
                        'cloud_vis_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'cloud_visible_diffuse'
                                  },
                        'net_solar':{
                                  'units': 'W/m^2',
                                  'long_name': 'net_solar_radiation'
                                  },
                        'veg_ir_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'vegetation_infrared_beam'
                                  },
                        'veg_ir_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'vegetation_infrared_diffuse'
                                  },
                        'veg_vis_beam':{
                                  'units': 'W/m^2',
                                  'long_name': 'vegetation_visible_beam'
                                  },
                        'veg_vis_diffuse':{
                                  'units': 'W/m^2',
                                  'long_name': 'vegetation_visible_diffuse'
                                  }
                        }
    
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
        
                
        self._logger.debug('Created distribute.solar')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
            
        """
        
        self._logger.debug('Initializing distribute.solar')
        
        self._initialize(topo, metadata)
        self.veg_height = topo.veg_height
        self.veg_tau = topo.veg_tau
        self.veg_k = topo.veg_k
        
        
    
    def distribute(self, data, illum_ang, cosz, azimuth, min_storm_day, albedo_vis, albedo_ir):
        """
        Distribute solar
        
        Args:
            data: cloud_factor data frame
            cosz: cosine of the zenith angle for the basin
            azimuth: azimuth to the sun for the basin 
            min_storm_day: decimal day of last storm for the entire basin
            
            
        """
    
        self._logger.debug('%s Distributing solar' % data.name)
        
        # cloud must always be distributed since it is used by thermal
        self._distribute(data, other_attribute='cloud_factor')
        
        # only need to calculate solar if the sun is up
        if cosz > 0:
            
            # get the current day of water year
            wy_day, wyear = utils.water_day(data.name)
            
            # determine the minutes west of timezone
            tz_min_west = np.abs(data.name.utcoffset().total_seconds()/60)
            
               
            #------------------------------------------------------------------------------ 
            # calculate clear sky radiation
                    
            # call the calc_ir and calc_vis to run as different processes
            ti = Process(target=self.calc_ir, args=(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth))
            ti.start()
                         
            tv = Process(target=self.calc_vis, args=(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth))
            tv.start()
             
            # wait for the processes to stop
            ti.join()
            tv.join()
            

            # load clear sky files back in
            vis = ipw.IPW(self.vis_file)
            self.clear_vis_beam = vis.bands[0].data
            self.clear_vis_diffuse = vis.bands[1].data
            
            ir = ipw.IPW(self.ir_file)
            self.clear_ir_beam = ir.bands[0].data
            self.clear_ir_diffuse = ir.bands[1].data
            
            #------------------------------------------------------------------------------ 
            # correct clear sky for cloud
            
            self._logger.debug('Correcting clear sky radiation for clouds')
            self.cloud_vis_beam, self.cloud_vis_diffuse = radiation.cf_cloud(self.clear_vis_beam, 
                                                                          self.clear_vis_diffuse, 
                                                                          self.cloud_factor)
            
            self.cloud_ir_beam, self.cloud_ir_diffuse = radiation.cf_cloud(self.clear_ir_beam, 
                                                                          self.clear_ir_diffuse, 
                                                                          self.cloud_factor)
            
            #------------------------------------------------------------------------------ 
            # correct cloud for veg
            
            self._logger.debug('Correcting radiation for vegitation')
                        
            ### calculate for visible ###
            # correct beam
            self.veg_vis_beam = radiation.veg_beam(self.cloud_vis_beam, self.veg_height, illum_ang, self.veg_k)
            
            # correct diffuse
            self.veg_vis_diffuse = radiation.veg_diffuse(self.cloud_vis_diffuse, self.veg_tau)
            
            ### calculate for ir ###
            # correct beam
            self.veg_ir_beam = radiation.veg_beam(self.cloud_ir_beam, self.veg_height, illum_ang, self.veg_k)
            
            # correct diffuse
            self.veg_ir_diffuse = radiation.veg_diffuse(self.cloud_ir_diffuse, self.veg_tau)
            
            
            #------------------------------------------------------------------------------ 
            # calculate net radiation
            
            self._logger.debug('Calculing net radiation')
            
            # calculate net visible
            vv_n = (self.veg_vis_beam + self.veg_vis_diffuse) * (1 - albedo_vis) 
            vv_n = utils.set_min_max(vv_n, self.min, self.max) # ensure min and max's are met
            
            # calculate net ir
            vir_n = (self.veg_ir_beam + self.veg_ir_diffuse) * (1 - albedo_ir) 
            vir_n = utils.set_min_max(vir_n, self.min, self.max) # ensure min and max's are met
            
            # calculate total net
            self.net_solar = vv_n + vir_n
            self.net_solar = utils.set_min_max(self.net_solar, self.min, self.max) # ensure min and max's are met
    
        else:
            
            self._logger.debug('Sun is down, see you in the morning!')
            
            # clear sky
#             z = np.zeros()

            self.clear_vis_beam = None
            self.clear_vis_diffuse = None
            self.clear_ir_beam = None
            self.clear_ir_diffuse = None
            
            # cloud
            self.cloud_vis_beam = None
            self.cloud_vis_diffuse = None
            self.cloud_ir_beam = None
            self.cloud_ir_diffuse = None
            
            # canopy
            self.veg_vis_beam = None
            self.veg_vis_diffuse = None
            self.veg_ir_beam = None
            self.veg_ir_diffuse = None
            
            # net
            self.net_solar = None
    
     
    def distribute_thread(self, queue, data):
        """
        Distribute the data using threading and queue
        
        Args:
            queue: queue dict for all variables
            data: cloud_factor
        
        Output:
            Changes the queue net_solar, cloud_factor
                for the given date
        """
        
        for t in data.index:
                        
            illum_ang = queue['illum_ang'].get(t)
            cosz = queue['cosz'].get(t)
            azimuth = queue['azimuth'].get(t)
            min_storm_day = queue['last_storm_day_basin'].get(t)
            albedo_vis = queue['albedo_vis'].get(t)
            albedo_ir = queue['albedo_ir'].get(t)
            
            self.distribute(data.ix[t], illum_ang, cosz, azimuth, min_storm_day, albedo_vis, albedo_ir)
        
            queue['net_solar'].put( [t, self.net_solar] )
            queue['cloud_factor'].put( [t, self.cloud_factor] )
            
             
            
            
    def calc_ir(self, min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth):
        """
        Run stoporad for the ir bands
        Args:
            min_storm_day
            wy_day
            tz_min_west
            wyear
            cosz
            azimuth
        """
        self._logger.debug('Calculating clear sky radiation, ir')
        
        ir_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.7,2.8 -s %s'\
            ' -d %s -f %i -y %i -A %s,%s -a %i -m %i -c %i -D %s > %s' \
            % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
               str(self.config['clear_omega']), str(self.config['clear_gamma']), \
               str(min_storm_day), str(wy_day), tz_min_west, wyear, \
               str(cosz), str(azimuth), self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
               self.albedoConfig['dirt'], self.stoporad_in, self.ir_file)
            
        self._logger.debug(ir_cmd)
        
        irp = sp.Popen(ir_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']})
        
        stdoutdata, stderrdata = irp.communicate()
#         self._logger.debug(stdoutdata)
#         self._logger.debug(stderrdata)
    
        if irp.returncode != 0:
            raise Exception('Clear sky for IR failed')        
            
            
    def calc_vis(self, min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth):
        """
        Run stoporad for the ir bands
        Args:
            min_storm_day
            wy_day
            tz_min_west
            wyear
            cosz
            azimuth
        """
        self._logger.debug('Calculating clear sky radiation, visible')
        
        vis_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.28,0.7 -s %s'\
            ' -d %s -f %i -y %i -A %s,%s -a %i -m %i -c %i -D %s > %s' \
            % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
               str(self.config['clear_omega']), str(self.config['clear_gamma']), \
               str(min_storm_day), str(wy_day), tz_min_west, wyear, \
               str(cosz), str(azimuth), self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
               self.albedoConfig['dirt'], self.stoporad_in, self.vis_file)
        self._logger.debug(vis_cmd)
            
        visp = sp.Popen(vis_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']})

        stdoutdata, stderrdata = visp.communicate()
#         self._logger.debug(stdoutdata)
#         self._logger.debug(stderrdata)

        if visp.returncode != 0:
            raise Exception('Clear sky for visible failed')
            
            
    
    