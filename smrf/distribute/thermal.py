import numpy as np

from smrf.distribute import image_data
from smrf.envphys.constants import STEF_BOLTZ
from smrf.envphys.core import envphys_c
from smrf.envphys.thermal import clear_sky, cloud, vegetation
from smrf.utils import utils


class th(image_data.image_data):
    """
    The :mod:`~smrf.distribute.thermal.th` class allows for variable specific
    distributions that go beyond the base class.

    Thermal radiation, or long-wave radiation, is calculated based on the clear
    sky radiation emitted by the atmosphere. Multiple methods for calculating
    thermal radition exist and SMRF has 4 options for estimating clear sky
    thermal radiation. Selecting one of the options below will change the
    equations used. The methods were chosen based on the study by Flerchinger
    et al (2009) :cite:`Flerchinger&al:2009` who performed a model comparison
    using 21 AmeriFlux sites from North America and China.

    Marks1979
        The methods follow those developed by Marks and Dozier (1979)
        :cite:`Marks&Dozier:1979` that calculates the effective clear sky
        atmospheric emissivity using the distributed air temperature,
        distributed dew point temperature, and the elevation. The clear sky
        radiation is further adjusted for topographic affects based on the
        percent of the sky visible at any given point.

    Dilley1998
        .. math::
            L_{clear} = 59.38 + 113.7 * \\left( \\frac{T_a}{273.16} \\right)^6
            + 96.96 \\sqrt{w/25}

        References: Dilley and O'Brian (1998) :cite:`Dilley&OBrian:1998`

    Prata1996
        .. math::
            \\epsilon_{clear} = 1 - (1 + w) * exp(-1.2 + 3w)^{1/2}

        References: Prata (1996) :cite:`Prata:1996`

    Angstrom1918
        .. math::
            \\epsilon_{clear} = 0.83 - 0.18 * 10^{-0.067 e_a}

        References: Angstrom (1918) :cite:`Angstrom:1918` as cited by Niemela
        et al (2001) :cite:`Niemela&al:2001`

    .. figure:: ../_static/thermal_comparison.png
       :alt: Comparing the 4 thermal methods.

       The 4 different methods for estimating clear sky thermal radiation for a
       single time step. As compared to the Mark1979 method, the other methods
       provide a wide range in the estimated value of thermal radiation.


    The topographic correct clear sky thermal radiation is further adjusted for
    cloud affects. Cloud correction is based on fraction of cloud cover, a
    cloud factor close to 1 meaning no clouds are present, there is little
    radiation added.  When clouds are present, or a cloud factor close to 0,
    then additional long wave radiation is added to account for the cloud
    cover. Selecting one of the options below will change the equations used.
    The methods were chosen based on the study by Flerchinger et al (2009)
    :cite:`Flerchinger&al:2009`, where :math:`c=1-cloud\\_factor`.

    Garen2005
        Cloud correction is based on the relationship in Garen and Marks (2005)
        :cite:`Garen&Marks:2005` between the cloud factor and measured long
        wave radiation using measurement stations in the Boise River Basin.

        .. math::
            L_{cloud} = L_{clear} * (1.485 - 0.488 * cloud\\_factor)

    Unsworth1975
        .. math::

            L_d &= L_{clear} + \\tau_8 c f_8 \\sigma T^{4}_{c}

            \\tau_8 &= 1 - \\epsilon_{8z} (1.4 - 0.4 \\epsilon_{8z})

            \\epsilon_{8z} &= 0.24 + 2.98 \\times 10^{-6} e^2_o exp(3000/T_o)

            f_8 &= -0.6732 + 0.6240 \\times 10^{-2} T_c - 0.9140
            \\times 10^{-5} T^2_c

        References: Unsworth and Monteith (1975) :cite:`Unsworth&Monteith:1975`

    Kimball1982
        .. math::
            L_d &= L_{clear} + \\tau_8 c \\sigma T^4_c


        where the original Kimball et al. (1982) :cite:`Kimball&al:1982` was
        for multiple cloud layers, which was simplified to one layer.
        :math:`T_c` is the cloud temperature and is assumed to be 11 K cooler
        than :math:`T_a`.

        References: Kimball et al. (1982) :cite:`Kimball&al:1982`

    Crawford1999
        .. math::
            \\epsilon_a = (1 - cloud\\_factor) + cloud\\_factor *
            \\epsilon_{clear}

        References: Crawford and Duchon (1999) :cite:`Crawford&Duchon:1999`
        where :math:`cloud\\_factor` is the ratio of measured solar radiation
        to the clear sky irradiance.

    The results from Flerchinger et al (2009) :cite:`Flerchinger&al:2009`
    showed that the Kimball1982 cloud correction with Dilley1998 clear sky
    algorthim had the lowest RMSD. The Crawford1999 worked best when combined
    with Angstrom1918, Dilley1998, or Prata1996.

    .. figure:: ../_static/thermal_cloud_comparision.png
       :alt: Comparing the 4 thermal cloud correction methods.

       The 4 different methods for correcting clear sky thermal radiation for
       cloud affects at a single time step. As compared to the Garen2005
       method, the other methods are typically higher where clouds are present
       (i.e. the lower left) where the cloud factor is around 0.4.

    The thermal radiation is further adjusted for canopy cover after the work
    of Link and Marks (1999) :cite:`Link&Marks:1999`. The correction is based
    on the vegetation's transmissivity, with the canopy temperature assumed to
    be the air temperature for vegetation greater than 2 meters.  The thermal
    radiation is adjusted by

    .. math::
        L_{canopy} = \\tau_d * L_{cloud} + (1 - \\tau_d) \\epsilon
        \\sigma T_a^4

    where :math:`\\tau_d` is the optical transmissivity, :math:`L_{cloud}` is
    the cloud corrected thermal radiation, :math:`\\epsilon` is the emissivity
    of the canopy (0.96), :math:`\\sigma` is the Stephan-Boltzmann constant,
    and :math:`T_a` is the distributed air temperature.

    Args:
        thermalConfig: The [thermal] section of the configuration file

    Attributes:
        config: configuration from [thermal] section
        thermal: numpy array of the precipitation
        min: minimum value of thermal is -600 W/m^2
        max: maximum value of thermal is 600 W/m^2
        stations: stations to be used in alphabetical order
        dem: numpy array for the DEM, from
            :py:attr:`smrf.data.loadTopo.Topo.dem`
        veg_type: numpy array for the veg type, from
            :py:attr:`smrf.data.loadTopo.Topo.veg_type`
        veg_height: numpy array for the veg height, from
            :py:attr:`smrf.data.loadTopo.Topo.veg_height`
        veg_k: numpy array for the veg K, from
            :py:attr:`smrf.data.loadTopo.Topo.veg_k`
        veg_tau: numpy array for the veg transmissivity, from
            :py:attr:`smrf.data.loadTopo.Topo.veg_tau`
        sky_view_factor: numpy array for the sky view factor, from
            :py:attr:`smrf.data.loadTopo.Topo.sky_view_factor`
    """

    variable = 'thermal'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'thermal': {
            'units': 'watt/m2',
            'standard_name': 'thermal_radiation',
            'long_name': 'Thermal (longwave) radiation'
        },
        'thermal_clear': {
            'units': 'watt/m2',
            'standard_name': 'thermal_radiation non-correct',
            'long_name': 'Thermal (longwave) radiation non-corrected'
        },
        'thermal_cloud': {
            'units': 'watt/m2',
            'standard_name': 'thermal_radiation cloud corrected',
            'long_name': 'Thermal (longwave) radiation cloud corrected'
        },
        'thermal_veg': {
            'units': 'watt/m2',
            'standard_name': 'thermal_radiation veg corrected',
            'long_name': 'Thermal (longwave) radiation veg corrected'
        }
    }
    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    BASE_THREAD_VARIABLES = frozenset([
        'thermal',
        'thermal_clear'
    ])

    def __init__(self, thermalConfig):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self.getConfig(thermalConfig)

        self.min = thermalConfig['min']
        self.max = thermalConfig['max']

        self.correct_cloud = self.config['correct_cloud']
        self.correct_veg = self.config['correct_veg']
        self.correct_terrain = self.config['correct_terrain']

        if self.correct_cloud:
            self.cloud_method = self.config['cloud_method']

        self.clear_sky_method = self.config['clear_sky_method']

        self._logger.debug('Created distribute.thermal')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, calls
        :mod:`smrf.distribute.image_data.image_data._initialize` for gridded
        distirbution. Sets the following from :mod:`smrf.data.loadTopo.Topo`

        * :py:attr:`veg_height`
        * :py:attr:`veg_tau`
        * :py:attr:`veg_k`
        * :py:attr:`sky_view_factor`
        * :py:attr:`dem`

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            data: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.thermal')
        self.date_time = date_time
        self._initialize(topo, data.metadata)

        self.veg_height = topo.veg_height
        self.veg_tau = topo.veg_tau
        self.veg_k = topo.veg_k
        self.sky_view_factor = topo.sky_view_factor
        if not self.correct_terrain:
            self.sky_view_factor = None
        self.dem = topo.dem

        if self.correct_cloud:
            self.add_thread_variables('thermal_cloud')

        if self.correct_veg:
            self.add_thread_variables('thermal_veg')

    def distribute(self, date_time, air_temp, vapor_pressure=None,
                   dew_point=None, cloud_factor=None):
        """
        Distribute for a single time step.

        The following steps are taken when distributing thermal:

        1. Calculate the clear sky thermal radiation from
            :mod:`smrf.envphys.core.envphys_c.ctopotherm`
        2. Correct the clear sky thermal for the distributed cloud factor
        3. Correct for canopy affects

        Args:
            date_time: datetime object for the current step
            air_temp: distributed air temperature for the time step
            vapor_pressure: distributed vapor pressure for the time step
            dew_point: distributed dew point for the time step
            cloud_factor: distributed cloud factor for the time step
                measured/modeled
        """

        self._logger.debug('%s Distributing thermal' % date_time)

        # calculate clear sky thermal
        if self.clear_sky_method == 'marks1979':
            cth = np.zeros_like(air_temp, dtype=np.float64)
            envphys_c.ctopotherm(
                air_temp, dew_point,
                self.dem,
                self.sky_view_factor,
                cth,
                self.config['marks1979_nthreads'])

        elif self.clear_sky_method == 'dilley1998':
            cth = clear_sky.Dilly1998(air_temp, vapor_pressure/1000)

        elif self.clear_sky_method == 'prata1996':
            cth = clear_sky.Prata1996(air_temp, vapor_pressure/1000)

        elif self.clear_sky_method == 'angstrom1918':
            cth = clear_sky.Angstrom1918(air_temp, vapor_pressure/1000)

        # terrain factor correction
        if (self.sky_view_factor is not None) and \
                (self.clear_sky_method != 'marks1979'):
            # apply (emiss * skvfac) + (1.0 - skvfac) to the longwave
            cth = cth * self.sky_view_factor + (1.0 - self.sky_view_factor) * \
                STEF_BOLTZ * air_temp**4

        # make output variable
        self.thermal_clear = cth.copy()

        # correct for the cloud factor
        # ratio of measured/modeled solar indicates the thermal correction
        if self.correct_cloud:
            if self.cloud_method == 'garen2005':
                cth = cloud.Garen2005(cth,
                                      cloud_factor)

            elif self.cloud_method == 'unsworth1975':
                cth = cloud.Unsworth1975(cth,
                                         air_temp,
                                         cloud_factor)

            elif self.cloud_method == 'kimball1982':
                cth = cloud.Kimball1982(cth,
                                        air_temp,
                                        vapor_pressure/1000,
                                        cloud_factor)

            elif self.cloud_method == 'crawford1999':
                cth = cloud.Crawford1999(cth,
                                         air_temp,
                                         cloud_factor)

            # make output variable
            self.thermal_cloud = cth.copy()

        # correct for vegetation
        if self.correct_veg:
            cth = vegetation.thermal_correct_canopy(cth,
                                                    air_temp,
                                                    self.veg_tau,
                                                    self.veg_height)

            # make output variable
            self.thermal_veg = cth.copy()

        self.thermal = utils.set_min_max(cth, self.min, self.max)

    def distribute_thread(self, smrf_queue, data_queue=None):
        """
        Distribute the data using threading. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.thermal.th.distribute` then puts the distributed
        data into the smrf_queue for :py:attr:`thermal`.

        Args:
            smrf_queue: smrf_queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time

        """

        for date_time in self.date_time:

            air_temp = smrf_queue['air_temp'].get(date_time)
            dew_point = smrf_queue['dew_point'].get(date_time)
            vapor_pressure = smrf_queue['vapor_pressure'].get(date_time)
            cloud_factor = smrf_queue['cloud_factor'].get(date_time)

            self.distribute(date_time, air_temp, vapor_pressure,
                            dew_point, cloud_factor)

            if self.correct_veg:
                smrf_queue['thermal_veg'].put(
                    [date_time, self.thermal_veg])
            if self.correct_cloud:
                smrf_queue['thermal_cloud'].put(
                    [date_time, self.thermal_cloud])

            smrf_queue['thermal_clear'].put([date_time, self.thermal_clear])

            smrf_queue['thermal'].put([date_time, self.thermal])
