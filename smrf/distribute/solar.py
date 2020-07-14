from smrf.distribute import image_data
from smrf.envphys.constants import IR_WAVELENGTHS, VISIBLE_WAVELENGTHS
from smrf.envphys.solar import cloud, toporad, vegetation
from smrf.utils import utils


class Solar(image_data.image_data):
    """
    The :mod:`~smrf.distribute.solar.solar` class allows for variable specific
    distributions that go beyond the base class.

    Multiple steps are required to estimate solar radiation:

    1. Terrain corrected clear sky radiation
    2. Adjust solar radiation for vegetation effects
    3. Calculate net radiation using the albedo

    The Image Processing Workbench (IPW) includes a utility ``stoporad`` to
    model terrain corrected clear sky radiation over the DEM. Within
    ``stoporad``, the radiation transfer model ``twostream`` simulates the
    clear sky radiation on a flat surface for a range of wavelengths through
    the atmosphere :cite:`Dozier:1980` :cite:`Dozier&Frew:1981`
    :cite:`Dubayah:1994`. Terrain correction using the DEM adjusts for terrain
    shading and splits the clear sky radiation into beam and diffuse radiation.

    The second step requires sites measuring solar radiation. The measured
    solar radiation is compared to the modeled clear sky radiation from
    ``twostream``. The cloud factor is then the measured incoming solar
    radiation divided by the modeled radiation.  The cloud factor can be
    computed on an hourly timescale if the measurement locations are of high
    quality. For stations that are less reliable, we recommend calculating a
    daily cloud factor which divides the daily integrated measured radiation by
    the daily integrated modeled radiation.  This helps to reduce the problems
    that may be encountered from instrument shading, instrument calibration, or
    a time shift in the data. The calculated cloud factor at each station can
    then be distrubted using any of the method available in
    :mod:`smrf.spatial`. Since the cloud factor is not explicitly controlled
    by elevation like other variables, the values may be distributed without
    detrending to elevation. The modeled clear sky radiation (both beam and
    diffuse)  are adjusted for clouds using
    :mod:`smrf.envphys.radiation.cf_cloud`.

    The third step adjusts the cloud corrected solar radiation for vegetation
    affects, following the methods developed by Link and Marks (1999)
    :cite:`Link&Marks:1999`. The direct beam radiation  is corrected by:

    .. math::
        R_b = S_b * exp( -\\mu h / cos \\theta )

    where :math:`S_b` is the above canopy direct radiation, :math:`\\mu` is
    the extinction coefficient (:math:`m^{-1}`), :math:`h` is the canopy height
    (:math:`m`), :math:`\\theta` is the solar zenith angle, and :math:`R_b` is
    the canopy adjusted direct radiation. Adjusting the diffuse radiation is
    performed by:

    .. math::
        R_d = \\tau * R_d

    where :math:`R_d` is the diffuse adjusted radiation, :math:`\\tau` is the
    optical transmissivity of the canopy, and :math:`R_d` is the above canopy
    diffuse radiation. Values for :math:`\\mu` and :math:`\\tau` can be found
    in Link and Marks (1999) :cite:`Link&Marks:1999`, measured at study sites
    in Saskatchewan and Manitoba.

    The final step for calculating the net solar radiation requires the surface
    albedo from :mod:`smrf.distribute.albedo`. The net radiation is the sum of
    the of beam and diffuse canopy adjusted radiation multipled by one minus
    the albedo.

    Args:
        config: full configuration dictionary contain at least the sections
                albedo, and solar
        topo: Topo class :mod:`smrf.data.loadTopo.Topo`

    Attributes:
        albedoConfig: configuration from [albedo] section
        config: configuration from [albedo] section
        clear_ir_beam: numpy array modeled clear sky infrared beam radiation
        clear_ir_diffuse: numpy array modeled clear sky infrared diffuse
            radiation
        clear_vis_beam: numpy array modeled clear sky visible beam radiation
        clear_vis_diffuse: numpy array modeled clear sky visible diffuse
            radiation
        cloud_factor: numpy array distributed cloud factor
        cloud_ir_beam: numpy array cloud adjusted infrared beam radiation
        cloud_ir_diffuse: numpy array cloud adjusted infrared diffuse radiation
        cloud_vis_beam: numpy array cloud adjusted visible beam radiation
        cloud_vis_diffuse: numpy array cloud adjusted visible diffuse radiation
        ir_file: temporary file from ``stoporad`` for infrared clear sky
            radiation
        metadata: metadata for the station data
        net_solar: numpy array for the calculated net solar radiation
        stations: stations to be used in alphabetical order
        veg_height: numpy array of vegetation heights from
            :mod:`smrf.data.loadTopo.Topo`
        veg_ir_beam: numpy array vegetation adjusted infrared beam radiation
        veg_ir_diffuse: numpy array vegetation adjusted infrared diffuse
            radiation
        veg_k: numpy array of vegetation extinction coefficient from
            :mod:`smrf.data.loadTopo.Topo`
        veg_tau: numpy array of vegetation optical transmissivity from
            :mod:`smrf.data.loadTopo.Topo`
        veg_vis_beam: numpy array vegetation adjusted visible beam radiation
        veg_vis_diffuse: numpy array vegetation adjusted visible diffuse
            radiation
        vis_file: temporary file from ``stoporad`` for visible clear sky
            radiation

    """

    variable = 'solar'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'clear_ir_beam': {
            'units': 'watt/m2',
            'standard_name': 'clear_sky_infrared_beam',
            'long_name': 'Clear sky infrared beam solar radiation'
        },
        'clear_ir_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'clear_sky_infrared_diffuse',
            'long_name': 'Clear sky infrared diffuse solar radiation'
        },
        'clear_vis_beam': {
            'units': 'watt/m2',
            'standard_name': 'clear_sky_visible_beam',
            'long_name': 'Clear sky visible beam solar radiation'
        },
        'clear_vis_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'clear_sky_visible_diffuse',
            'long_name': 'Clear sky visible diffuse solar radiation'
        },
        'cloud_ir_beam': {
            'units': 'watt/m2',
            'standard_name': 'cloud_infrared_beam',
            'long_name': 'Cloud corrected infrared beam solar radiation'
        },
        'cloud_ir_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'cloud_infrared_diffuse',
            'long_name': 'Cloud corrected infrared diffuse solar radiation'
        },
        'cloud_vis_beam': {
            'units': 'watt/m2',
            'standard_name': 'cloud_visible_beam',
            'long_name': 'Cloud corrected visible beam solar radiation'
        },
        'cloud_vis_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'cloud_visible_diffuse',
            'long_name': 'Cloud corrected visible diffuse solar radiation'
        },
        'net_solar': {
            'units': 'watt/m2',
            'standard_name': 'net_solar_radiation',
            'long_name': 'Net solar radiation'
        },
        'veg_ir_beam': {
            'units': 'watt/m2',
            'standard_name': 'vegetation_infrared_beam',
            'long_name': 'Vegetation corrected infrared beam solar radiation'
        },
        'veg_ir_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'vegetation_infrared_diffuse',
            'long_name': 'Vegetation corrected infrared diffuse solar \
                radiation'
        },
        'veg_vis_beam': {
            'units': 'watt/m2',
            'standard_name': 'vegetation_visible_beam',
            'long_name': 'Vegetation corrected visible beam solar radiation'
        },
        'veg_vis_diffuse': {
            'units': 'watt/m2',
            'standard_name': 'vegetation_visible_diffuse',
            'long_name': 'Vegetation corrected visible diffuse solar radiation'
        }
    }

    CLEAR_SKY_THREAD_VARIABLES = [
        'clear_ir_beam',
        'clear_ir_diffuse',
        'clear_vis_beam',
        'clear_vis_diffuse'
    ]

    VEG_THREAD_VARIABLES = [
        'veg_ir_beam',
        'veg_ir_diffuse',
        'veg_vis_beam',
        'veg_vis_diffuse'
    ]

    CLOUD_THREAD_VARIABLES = [
        'cloud_ir_beam',
        'cloud_ir_diffuse',
        'cloud_vis_beam',
        'cloud_vis_diffuse'
    ]

    BASE_THREAD_VARIABLES = frozenset(
        CLEAR_SKY_THREAD_VARIABLES +
        CLOUD_THREAD_VARIABLES +
        VEG_THREAD_VARIABLES +
        ['net_solar']
    )

    # These are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    def __init__(self, config, topo):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        self.config = config["solar"]
        self.albedoConfig = config["albedo"]

        self.topo = topo

        self._logger.debug('Created distribute.solar')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, soley calls
        :mod:`smrf.distribute.image_data.image_data._initialize`. Sets the
        following attributes:

        * :py:attr:`veg_height`
        * :py:attr:`veg_tau`
        * :py:attr:`veg_k`

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            data: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.solar')
        self.date_time = date_time
        # Solar has no stations. Relies on Cloud factor
        self.stations = None
        self._initialize(topo, data.metadata)
        self.veg_height = topo.veg_height
        self.veg_tau = topo.veg_tau
        self.veg_k = topo.veg_k

    def distribute(self, date_time, cloud_factor, illum_ang, cosz, azimuth,
                   albedo_vis, albedo_ir):
        """
        Distribute air temperature given a Panda's dataframe for a single time
        step. Calls :mod:`smrf.distribute.image_data.image_data._distribute`.

        If the sun is up, i.e. ``cosz > 0``, then the following steps are
        performed:

        1. Model clear sky radiation
        2. Cloud correct with :mod:`!smrf.distribute.solar.solar.cloud_correct`
        3. vegetation correct with
            :mod:`!smrf.distribute.solar.solar.veg_correct`
        4. Calculate net radiation with
            :mod:`!smrf.distribute.solar.solar.calc_net`

        If sun is down, then all calculated values will be set to ``None``,
        signaling the output functions to put zeros in their place.

        Args:
            cloud_factor: Numpy array of the domain for cloud factor
            cosz: cosine of the zenith angle for the basin, from
                :mod:`smrf.envphys.radiation.sunang`
            azimuth: azimuth to the sun for the basin, from
                :mod:`smrf.envphys.radiation.sunang`
            albedo_vis: numpy array for visible albedo, from
                :mod:`smrf.distribute.albedo.Albedo.albedo_vis`
            albedo_ir: numpy array for infrared albedo, from
                :mod:`smrf.distribute.albedo.Albedo.albedo_ir`

        """

        self._logger.debug(f'{date_time} Distributing solar')

        # Only calculate solar if the sun is up
        if cosz > 0:
            self.cloud_factor = cloud_factor.copy()

            # --------------------------------------------
            # calculate clear sky radiation

            # Not all the clean but it will work for now
            val_beam, val_diffuse = self.calc_stoporad(
                date_time, illum_ang, cosz, azimuth,
                albedo_ir, IR_WAVELENGTHS)

            setattr(self, 'clear_ir_beam', val_beam)
            setattr(self, 'clear_ir_diffuse', val_diffuse)
            self.ir_beam = val_beam.copy()
            self.ir_diffuse = val_diffuse.copy()

            val_beam, val_diffuse = self.calc_stoporad(
                date_time, illum_ang, cosz, azimuth,
                albedo_vis, VISIBLE_WAVELENGTHS)

            setattr(self, 'clear_vis_beam', val_beam)
            setattr(self, 'clear_vis_diffuse', val_diffuse)
            self.vis_beam = val_beam.copy()
            self.vis_diffuse = val_diffuse.copy()

            # --------------------------------------------
            # correct clear sky for cloud
            if self.config['correct_cloud']:
                self.cloud_correct()
                # copy output for output variables
                self.cloud_vis_beam = self.vis_beam.copy()
                self.cloud_vis_diffuse = self.vis_diffuse.copy()
                self.cloud_ir_beam = self.ir_beam.copy()
                self.cloud_ir_diffuse = self.ir_diffuse.copy()

            # --------------------------------------------
            # correct cloud for veg
            if self.config['correct_veg']:
                self.veg_correct(illum_ang)
                self.veg_vis_beam = self.vis_beam.copy()
                self.veg_vis_diffuse = self.vis_diffuse.copy()
                self.veg_ir_beam = self.ir_beam.copy()
                self.veg_ir_diffuse = self.ir_diffuse.copy()

            # --------------------------------------------
            # calculate net radiation
            self.calc_net(albedo_vis, albedo_ir)

        else:

            self._logger.debug('Sun is down, see you in the morning!')

            # clear sky
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

    def distribute_thread(self, smrf_queue, data_queue=None):
        """
        Distribute the data using threading. All data is provided and
        ``distribute_thread`` will go through each time step following the
        methods outlined in :mod:`smrf.distribute.solar.solar.distribute`. The
        data smrf_queues puts the distributed data into:

        * :py:attr:`net_solar`

        Args:
            smrf_queue: smrf_queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        self._logger.info("Distributing {}".format(self.variable))
        for date_time in self.date_time:

            cosz = smrf_queue['cosz'].get(date_time)
            azimuth = smrf_queue['azimuth'].get(date_time)
            illum_ang = smrf_queue['illum_ang'].get(date_time)
            albedo_ir = smrf_queue['albedo_ir'].get(date_time)
            albedo_vis = smrf_queue['albedo_vis'].get(date_time)
            self.cloud_factor = smrf_queue['cloud_factor'].get(date_time)

            self.distribute(
                date_time,
                self.cloud_factor,
                illum_ang,
                cosz,
                azimuth,
                albedo_vis,
                albedo_ir)

            for cstv in self.CLEAR_SKY_THREAD_VARIABLES:
                smrf_queue[cstv].put([date_time, getattr(self, cstv)])

            # Add the cloud corrected variables to the smrf_queue
            if self.config['correct_cloud']:
                for vtv in self.VEG_THREAD_VARIABLES:
                    smrf_queue[vtv].put([date_time, getattr(self, vtv)])

            # Add the veg correct variables to the smrf_queue
            if self.config['correct_veg']:
                for ctv in self.CLOUD_THREAD_VARIABLES:
                    smrf_queue[ctv].put([date_time, getattr(self, ctv)])

            smrf_queue['net_solar'].put([date_time, self.net_solar])

    def cloud_correct(self):
        """
        Correct the modeled clear sky radiation for cloud cover using
        :mod:`smrf.envphys.radiation.cloud.cf_cloud`.
        Sets :py:attr:`cloud_vis_beam` and :py:attr:`cloud_vis_diffuse`.
        """

        self._logger.debug('Correcting clear sky radiation for clouds')
        self.vis_beam, self.vis_diffuse = cloud.cf_cloud(
            self.vis_beam,
            self.vis_diffuse,
            self.cloud_factor)

        self.ir_beam, self.ir_diffuse = cloud.cf_cloud(
            self.ir_beam,
            self.ir_diffuse,
            self.cloud_factor)

    def veg_correct(self, illum_ang):
        """
        Correct the cloud adjusted radiation for vegetation using
        :mod:`smrf.envphys.radiation.vegetation.veg_beam` and
        :mod:`smrf.envphys.radiation.vegetation.veg_diffuse`. Sets
        :py:attr:`veg_vis_beam`, :py:attr:`veg_vis_diffuse`,
        :py:attr:`veg_ir_beam`, and :py:attr:`veg_ir_diffuse`.

        Args:
            illum_ang: numpy array of the illumination angle over the DEM, from
                :mod:`smrf.envphys.radiation.sunang`

        """

        self._logger.debug('Correcting radiation for vegetation')

        # calculate for visible
        # correct beam
        self.vis_beam = vegetation.solar_veg_beam(
            self.vis_beam,
            self.veg_height,
            illum_ang,
            self.veg_k)

        # correct diffuse
        self.vis_diffuse = vegetation.solar_veg_diffuse(
            self.vis_diffuse,
            self.veg_tau)

        # calculate for ir
        # correct beam
        self.ir_beam = vegetation.solar_veg_beam(
            self.ir_beam,
            self.veg_height,
            illum_ang,
            self.veg_k)

        # correct diffuse
        self.ir_diffuse = vegetation.solar_veg_diffuse(
            self.ir_diffuse,
            self.veg_tau)

    def calc_net(self, albedo_vis, albedo_ir):
        """
        Calculate the net radiation using the vegetation adjusted radiation.
        Sets :py:attr:`net_solar`.

        Args:
            albedo_vis: numpy array for visible albedo, from
                :mod:`smrf.distribute.albedo.Albedo.albedo_vis`
            albedo_ir: numpy array for infrared albedo, from
                :mod:`smrf.distribute.albedo.Albedo.albedo_ir`
        """

        self._logger.debug('Calculating net radiation')

        # calculate net visible
        vv_n = (self.vis_beam + self.vis_diffuse) * (1 - albedo_vis)
        vv_n = utils.set_min_max(vv_n, self.min, self.max)

        # calculate net ir
        vir_n = (self.ir_beam + self.ir_diffuse) * (1 - albedo_ir)
        vir_n = utils.set_min_max(vir_n, self.min, self.max)

        # calculate total net
        self.net_solar = vv_n + vir_n
        self.net_solar = utils.set_min_max(self.net_solar, self.min, self.max)

    def calc_stoporad(self, date_time, illum_ang, cosz, azimuth,
                      albedo_surface, wavelength_range=VISIBLE_WAVELENGTHS):
        """Run stoporad for the given date_time and wavelength range

        Args:
            date_time (datetime): datetime object
            illum_ang (np.array): numpy array of cosing of local illumination
                angles
            cosz (float): cosine of the zenith angle for the basin
            azimuth (float): azimuth to the sun for the basin
            albedo_surface (np.array): albedo should match wavelengths
                specified
            wavelength_range (list, optional): wavelengths to integrate over.
                Defaults to [0.28, 0.7].

        Returns:
            tuple: clear sky beam and diffuse radiation
        """

        clear_beam, clear_diffuse = toporad.stoporad(
            date_time,
            self.topo,
            cosz,
            azimuth,
            illum_ang,
            albedo_surface,
            wavelength_range=wavelength_range,
            tau_elevation=self.config['clear_opt_depth'],
            tau=self.config['clear_tau'],
            omega=self.config['clear_omega'],
            scattering_factor=self.config['clear_gamma'])

        return clear_beam, clear_diffuse
