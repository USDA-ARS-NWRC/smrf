__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-06"
__version__ = "0.0.1"

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
    The :mod:`~smrf.distribute.solar.solar` class allows for variable specific distributions that 
    go beyond the base class.
    
    Multiple steps are required to estimate solar radiation:
    
    1. Terrain corrected clear sky radiation
    2. Distribute a cloud factor and adjust modeled clear sky
    3. Adjust solar radiation for vegitation effects
    4. Calculate net radiation using the albedo
    
    The Image Processing Workbench (IPW) includes a utility ``stoporad`` to model terrain corrected
    clear sky radiation over the DEM. Within ``stoporad``, the radiation transfer model ``twostream``
    simulates the clear sky radiation on a flat surface for a range of wavelengths through the atmosphere
    :cite:`Dozier:1980` :cite:`Dozier&Frew:1981` :cite:`Dubayah:1994`. Terrain correction using the DEM
    adjusts for terrain shading and splits the clear sky radiation into beam and diffuse radiation.
    
    The second step requires sites measuring solar radiation. The measured solar radiation is compared
    to the modeled clear sky radiation from ``twostream``. The cloud factor is then the measured incoming
    solar radiation divided by the modeled radiation.  The cloud factor can be computed on an hourly
    timescale if the measurement locations are of high quality. For stations that are less reliable, we
    recommend calculating a daily cloud factor which divides the daily integrated measured radiation by
    the daily integrated modeled radiation.  This helps to reduce the problems that may be encountered from
    instrument shading, instrument calibration, or a time shift in the data. The calculated cloud factor
    at each station can then be distrubted using any of the method available in :mod:`smrf.spatial`.
    Since the cloud factor is not explicitly controlled by elevation like other variables, the values may
    be distributed without detrending to elevation. The modeled clear sky radiation (both beam and diffuse)
    are adjusted for clouds using :mod:`smrf.envphys.radiation.cf_cloud`.
    
    The third step adjusts the cloud corrected solar radiation for vegitation affects, following the
    methods developed by Link and Marks (1999) :cite:`Link&Marks:1999`. The direct beam radiation
    is corrected by:
    
    .. math::
        R_b = S_b * exp( -\\mu h / cos \\theta )
        
    where :math:`S_b` is the above canopy direct radiation, :math:`\\mu` is the extinction coefficient
    (:math:`m^{-1}`), :math:`h` is the canopy height (:math:`m`), :math:`\\theta` is the solar zenith
    angle, and :math:`R_b` is the canopy adjusted direct radiation. Adjusting the diffuse radiation is
    performed by:
    
    .. math::
        R_d = \\tau * R_d
        
    where :math:`R_d` is the diffuse adjusted radiation, :math:`\\tau` is the optical transmissivity of
    the canopy, and :math:`R_d` is the above canopy diffuse radiation. Values for :math:`\\mu` and
    :math:`\\tau` can be found in Link and Marks (1999) :cite:`Link&Marks:1999`, measured at study sites
    in Saskatchewan and Manitoba.
    
    The final step for calculating the net solar radiation requires the surface albedo from 
    :mod:`smrf.distribute.albedo`. The net radiation is the sum of the of beam and diffuse canopy 
    adjusted radiation multipled by one minus the albedo.
    
    Args:
        solarConfig: configuration from [solar] section
        albedoConfig: configuration from [albedo] section
        stoporad_in: file path to the stoporad_in file created from :mod:`smrf.data.loadTopo.topo`
        tempDir: location of temp/working directory (default=None, which is the 'TMPDIR' environment variable)
    
    Attributes:
        config: configuration from [solar] section
        albedoConfig: configuration from [albedo] section
        stoporad_in: file path to the stoporad_in file created from :mod:`smrf.data.loadTopo.topo`
        clear_ir_beam: numpy array modeled clear sky infrared beam radiation
        clear_ir_diffuse: numpy array modeled clear sky infrared diffuse radiation
        clear_vis_beam: numpy array modeled clear sky visible beam radiation
        clear_vis_diffuse: numpy array modeled clear sky visible diffuse radiation
        cloud_factor: numpy array distributed cloud factor
        cloud_ir_beam: numpy array cloud adjusted infrared beam radiation
        cloud_ir_diffuse: numpy array cloud adjusted infrared diffuse radiation
        cloud_vis_beam: numpy array cloud adjusted visible beam radiation
        cloud_vis_diffuse: numpy array cloud adjusted visible diffuse radiation
        ir_file: temporary file from ``stoporad`` for infrared clear sky radiation
        metadata: metadata for the station data
        net_solar: numpy array for the calculated net solar radiation
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.air_temp.ta`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        stations: stations to be used in alphabetical order
        stoporad_in: file path to the stoporad_in file created from :mod:`smrf.data.loadTopo.topo` 
        tempDir: temporary directory for ``stoporad``, will default to the ``TMPDIR`` environment variable
        variable: solar
        veg_height: numpy array of vegitation heights from :mod:`smrf.data.loadTopo.topo` 
        veg_ir_beam: numpy array vegitation adjusted infrared beam radiation
        veg_ir_diffuse: numpy array vegitation adjusted infrared diffuse radiation
        veg_k: numpy array of vegitation extinction coefficient from :mod:`smrf.data.loadTopo.topo` 
        veg_tau: numpy array of vegitation optical transmissivity from :mod:`smrf.data.loadTopo.topo` 
        veg_vis_beam: numpy array vegitation adjusted visible beam radiation
        veg_vis_diffuse: numpy array vegitation adjusted visible diffuse radiation
        vis_file: temporary file from ``stoporad`` for visible clear sky radiation
    
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
        Initialize the distribution, soley calls :mod:`smrf.distribute.image_data.image_data._initialize`.
        Sets the following attributes:
        
        * :py:attr:`veg_height`
        * :py:attr:`veg_tau`
        * :py:attr:`veg_k`
        
        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`
            
        """
        
        self._logger.debug('Initializing distribute.solar')
        
        self._initialize(topo, metadata)
        self.veg_height = topo.veg_height
        self.veg_tau = topo.veg_tau
        self.veg_k = topo.veg_k
        
        
    
    def distribute(self, data, illum_ang, cosz, azimuth, min_storm_day, albedo_vis, albedo_ir):
        """
        Distribute air temperature given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.
        
        If the sun is up, i.e. ``cosz > 0``, then the following steps are performed:
        
        1. Distribute cloud factor
        2. Model clear sky radiation
        3. Cloud correct with :mod:`!smrf.distribute.solar.solar.cloud_correct`
        4. Vegitation correct with :mod:`!smrf.distribute.solar.solar.veg_correct`
        5. Calculate net radiation with :mod:`!smrf.distribute.solar.solar.calc_net`
        
        If sun is down, then all calculated values will be set to ``None``, signaling the output functions
        to put zeros in their place.
        
        Args:
            data: Pandas dataframe for a single time step from cloud_factor
            cosz: cosine of the zenith angle for the basin, from :mod:`smrf.envphys.radiation.sunang`
            azimuth: azimuth to the sun for the basin, from :mod:`smrf.envphys.radiation.sunang`
            min_storm_day: decimal day of last storm for the entire basin, from :mod:`smrf.distribute.precip.ppt.last_storm_day_basin`
            albedo_vis: numpy array for visible albedo, from :mod:`smrf.distribute.albedo.albedo.albedo_vis`
            albedo_ir: numpy array for infrared albedo, from :mod:`smrf.distribute.albedo.albedo.albedo_ir`
            
        """
    
        self._logger.debug('%s Distributing solar' % data.name)
        
        # cloud must always be distributed since it is used by thermal
        self._distribute(data, other_attribute='cloud_factor')
        
        # only need to calculate solar if the sun is up
        if cosz > 0:
            
            wy_day, wyear, tz_min_west = self.radiation_dates(data.name)
            
               
            #------------------------------------------------------------------------------ 
            # calculate clear sky radiation
                    
#             # call the calc_ir and calc_vis to run as different processes
#             ti = Process(target=self.calc_ir, args=(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth))
#             ti.start()
#                           
#             tv = Process(target=self.calc_vis, args=(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth))
#             tv.start()
#               
#             # wait for the processes to stop
#             ti.join()
#             tv.join()
            
            # not all the clean but it will work for now
            val_beam, val_diffuse = self.calc_ir(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth)
            setattr(self, 'clear_ir_beam', val_beam)
            setattr(self, 'clear_ir_diffuse', val_diffuse)
            
            val_beam, val_diffuse = self.calc_vis(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth)
            setattr(self, 'clear_vis_beam', val_beam)
            setattr(self, 'clear_vis_diffuse', val_diffuse)
            
            #------------------------------------------------------------------------------ 
            # correct clear sky for cloud
            
            self.cloud_correct()
            
            #------------------------------------------------------------------------------ 
            # correct cloud for veg
            
            self.veg_correct(illum_ang)
            
            
            #------------------------------------------------------------------------------ 
            # calculate net radiation
            
            self.calc_net(albedo_vis, albedo_ir)
    
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
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step following the methods outlined in 
        :mod:`smrf.distribute.solar.solar.distribute`. The data queues puts the distributed data into:
        
        * :py:attr:`net_solar`
        * :py:attr:`cloud_factor`
        
         
        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        
        for t in data.index:
            
            # distribute the cloud factor
            self._distribute(data.ix[t], other_attribute='cloud_factor')
            
            # check if sun is up or not
            cosz = queue['cosz'].get(t)
            
            if cosz > 0:
                
                # get the clear sky, set class attributes
                setattr(self, 'clear_vis_beam', queue['clear_vis_beam'].get(t))
                setattr(self, 'clear_vis_diffuse', queue['clear_vis_diffuse'].get(t))
                setattr(self, 'clear_ir_beam', queue['clear_ir_beam'].get(t))
                setattr(self, 'clear_ir_diffuse', queue['clear_ir_diffuse'].get(t))
                
                # correct clear sky for cloud
                self.cloud_correct()
                
                # correct cloud for veg
                illum_ang = queue['illum_ang'].get(t)
                self.veg_correct(illum_ang)
                
                # get the albedo from the queue
                albedo_vis = queue['albedo_vis'].get(t)
                albedo_ir = queue['albedo_ir'].get(t)
                
                # calculate net radiation
                self.calc_net(albedo_vis, albedo_ir)
            
            else:
                self.net_solar = None
                
        
            queue['net_solar'].put( [t, self.net_solar] )
            queue['cloud_factor'].put( [t, self.cloud_factor] )
            
    
    def distribute_thread_clear(self, queue, data, calc_type):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and model clear sky radiation with ``stoporad``. The data 
        queues puts the distributed data into:
        
        * :py:attr:`clear_vis_beam`
        * :py:attr:`clear_vis_diffuse`
        * :py:attr:`clear_ir_beam`
        * :py:attr:`clear_ir_diffuse`
                
        """
        
        # the variable names
        beam = '%s_beam' % calc_type
        diffuse = '%s_diffuse' % calc_type
        
        for t in data.index:
            
            # check if sun is up or not
            cosz = queue['cosz'].get(t)
            
            if cosz > 0:
            
                # get the rest of the information
                azimuth = queue['azimuth'].get(t)
                min_storm_day = queue['last_storm_day_basin'].get(t)
            
                wy_day, wyear, tz_min_west = self.radiation_dates(t)
            
                if calc_type == 'clear_ir':
                    val_beam, val_diffuse = self.calc_ir(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth)
                elif calc_type == 'clear_vis':          
                    val_beam, val_diffuse = self.calc_vis(min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth)
                else:
                    raise Exception('Could not determine type of clear sky radiation to calculate')
                
            else:
                val_beam = None
                val_diffuse = None
                
            # put into the queue
            queue[beam].put([t, val_beam])
            queue[diffuse].put([t, val_diffuse])
            
             
             
    def cloud_correct(self):
        """
        Correct the modeled clear sky radiation for cloud cover using :mod:`smrf.envphys.radiation.cf_cloud`.
        Sets :py:attr:`cloud_vis_beam` and :py:attr:`cloud_vis_diffuse`.
        """
        
        self._logger.debug('Correcting clear sky radiation for clouds')
        self.cloud_vis_beam, self.cloud_vis_diffuse = radiation.cf_cloud(self.clear_vis_beam, 
                                                                      self.clear_vis_diffuse, 
                                                                      self.cloud_factor)
        
        self.cloud_ir_beam, self.cloud_ir_diffuse = radiation.cf_cloud(self.clear_ir_beam, 
                                                                      self.clear_ir_diffuse, 
                                                                      self.cloud_factor)
        
        
    def veg_correct(self, illum_ang):
        """
        Correct the cloud adjusted radiation for vegitation using :mod:`smrf.envphys.radiation.veg_beam`
        and :mod:`smrf.envphys.radiation.veg_diffuse`. Sets :py:attr:`veg_vis_beam`, :py:attr:`veg_vis_diffuse`
        :py:attr:`veg_ir_beam`, and :py:attr:`veg_ir_diffuse`.
        
        Args:
            illum_ang: numpy array of the illumination angle over the DEM, from :mod:`smrf.envphys.radiation.sunang`
        
        """
        
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
        
     
    def calc_net(self, albedo_vis, albedo_ir):
        """
        Calculate the net radiation using the vegitation adjusted radiation. Sets :py:attr:`net_solar`.
        
        Args:
            albedo_vis: numpy array for visible albedo, from :mod:`smrf.distribute.albedo.albedo.albedo_vis`
            albedo_ir: numpy array for infrared albedo, from :mod:`smrf.distribute.albedo.albedo.albedo_ir`
        """
        
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
        
            
    def calc_ir(self, min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth):
        """
        Run ``stoporad`` for the infrared bands
    
        Args:
            min_storm_day: decimal day of last storm for the entire basin, from :mod:`smrf.distribute.precip.ppt.last_storm_day_basin`
            wy_day: day of water year, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            tz_min_west: time zone in minutes west from UTC, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            wyear: water year, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            cosz: cosine of the zenith angle for the basin, from :mod:`smrf.envphys.radiation.sunang`
            azimuth: azimuth to the sun for the basin, from :mod:`smrf.envphys.radiation.sunang`
        """
        self._logger.debug('Calculating clear sky radiation, ir')
        
        ir_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.7,2.8 -s %s'\
            ' -d %s -f %i -y %i -A %f,%f -a %i -m %i -c %i -D %s > %s' \
            % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
               str(self.config['clear_omega']), str(self.config['clear_gamma']), \
               str(min_storm_day), str(wy_day), tz_min_west, wyear, \
               cosz, azimuth, self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
               self.albedoConfig['dirt'], self.stoporad_in, self.ir_file)
            
#         self._logger.debug(ir_cmd)
        
        irp = sp.Popen(ir_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']})
        
        stdoutdata, stderrdata = irp.communicate()
    
        if irp.returncode != 0:
            raise Exception('Clear sky for IR failed')
        
        ir = ipw.IPW(self.ir_file)
        clear_ir_beam = ir.bands[0].data
        clear_ir_diffuse = ir.bands[1].data
        
        return clear_ir_beam, clear_ir_diffuse   
            
            
    def calc_vis(self, min_storm_day, wy_day, tz_min_west, wyear, cosz, azimuth):
        """
        Run ``stoporad`` for the visible bands
        
        Args:
            min_storm_day: decimal day of last storm for the entire basin, from :mod:`smrf.distribute.precip.ppt.last_storm_day_basin`
            wy_day: day of water year, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            tz_min_west: time zone in minutes west from UTC, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            wyear: water year, from :mod:`~smrf.distirbute.solar.solar.radiation_dates`
            cosz: cosine of the zenith angle for the basin, from :mod:`smrf.envphys.radiation.sunang`
            azimuth: azimuth to the sun for the basin, from :mod:`smrf.envphys.radiation.sunang`
        """
        self._logger.debug('Calculating clear sky radiation, visible')
        
        vis_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.28,0.7 -s %s'\
            ' -d %s -f %i -y %i -A %f,%f -a %i -m %i -c %i -D %s > %s' \
            % (self.config['clear_opt_depth'], str(self.config['clear_tau']), \
               str(self.config['clear_omega']), str(self.config['clear_gamma']), \
               str(min_storm_day), str(wy_day), tz_min_west, wyear, \
               cosz, azimuth, self.albedoConfig['grain_size'], self.albedoConfig['max_grain'], \
               self.albedoConfig['dirt'], self.stoporad_in, self.vis_file)
#         self._logger.debug(vis_cmd)
            
        visp = sp.Popen(vis_cmd, shell=True, env={"PATH": os.environ['PATH'], "TMPDIR": os.environ['TMPDIR']})

        stdoutdata, stderrdata = visp.communicate()

        if visp.returncode != 0:
            raise Exception('Clear sky for visible failed')
        
        # load clear sky files back in
        vis = ipw.IPW(self.vis_file)
        clear_vis_beam = vis.bands[0].data
        clear_vis_diffuse = vis.bands[1].data
        
        return clear_vis_beam, clear_vis_diffuse
            
            
    def radiation_dates(self, date_time):
        """
        Calculate some times based on the date for ``stoporad``
        
        Args:
            date_time: date time object
            
        Returns:
            (tuple): tuple containing:
            
                * **wy_day** - day of water year from October 1
                * **wyear** - water year
                * **tz_min_west** - minutes west of UTC for timezone
        """
        
        # get the current day of water year
        wy_day, wyear = utils.water_day(date_time)
        
        # determine the minutes west of timezone
        tz_min_west = np.abs(date_time.utcoffset().total_seconds()/60)
        
        return wy_day, wyear, tz_min_west
    
