import logging
import os

import numpy as np
import pytz
from scipy import interpolate

from smrf.distribute import image_data
from smrf.utils import utils


def interpx(yi, xi, x):
    """Interpolate in on direction

    Arguments:
        yi {array} -- y data to fit
        xi {array} -- x data to fit
        x {array} -- x data to interpolate over

    Returns:
        array -- y values evaluated at x
    """
    s = interpolate.interp1d(xi, yi, fill_value='extrapolate')
    return s(x)


class WindNinjaModel(image_data.image_data):
    """The `WindNinjaModel` loads data from a WindNinja simulation.
    The WindNinja is ran externally to SMRF and the configuration
    points to the location of the output ascii files. SMRF takes the
    files and interpolates to the model domain.
    """

    VARIABLE = 'wind'
    WN_DATE_FORMAT = '%m-%d-%Y_%H%M'
    DATE_FORMAT = '%Y%m%d'

    def __init__(self, smrf_config):
        """Initialize the WinstralWindModel

        Arguments:
            smrf_config {UserConfig.Dictionary} -- entire smrf config
            distribute_drifts {bool} -- not used

        Raises:
            IOError: if maxus file does not match topo size
        """

        image_data.image_data.__init__(self, self.VARIABLE)

        self._logger = logging.getLogger(__name__)
        self._logger.debug('Creating the WindNinjaModel')

        self.smrf_config = smrf_config
        self.getConfig(smrf_config['wind'])

        # wind ninja parameters
        self.wind_ninja_dir = self.config['wind_ninja_dir']
        self.wind_ninja_dxy = self.config['wind_ninja_dxdy']
        self.wind_ninja_pref = self.config['wind_ninja_pref']
        if self.config['wind_ninja_tz'] is not None:
            self.wind_ninja_tz = pytz.timezone(
                self.config['wind_ninja_tz'].title())

        # self.start_date = pd.to_datetime(
        #     self.smrf_config['time']['start_date'])
        # self.grid_data = self.smrf_config['gridded']['data_type']

        self.init_interp = True
        self.flatwind = None
        self.dir_round_cell = None
        self.cellmaxus = None

    def wind_ninja_path(self, dt, file_type):
        """Generate the path to the wind ninja data and ensure
        it exists.

        Arguments:
            file_type {str} -- type of file to get
        """

        # convert the SMRF date time to the WindNinja time
        t_file = dt.astimezone(self.wind_ninja_tz)

        f_path = os.path.join(
            self.wind_ninja_dir,
            'data{}'.format(dt.strftime(self.DATE_FORMAT)),
            'wind_ninja_data',
            '{}_{}_{:d}m_{}.asc'.format(
                self.wind_ninja_pref,
                t_file.strftime(self.WN_DATE_FORMAT),
                self.wind_ninja_dxy,
                file_type
            ))

        if not os.path.isfile(f_path):
            raise ValueError(
                'WindNinja file does not exist: {}!'.format(f_path))

        return f_path

    def initialize(self, topo, data=None):
        """Initialize the model with data

        Arguments:
            topo {topo class} -- Topo class
            data {None} -- Not used but needs to be there
        """

        # meshgrid points
        self.X = topo.X
        self.Y = topo.Y

        self.model_dxdy = np.mean(np.diff(topo.x))

        # WindNinja output height in meters
        self.wind_height = float(self.config['wind_ninja_height'])

        # set roughness that was used in WindNinja simulation
        # WindNinja uses 0.01m for grass, 0.43 for shrubs, and 1.0 for forest
        self.wn_roughness = float(self.config['wind_ninja_roughness']) * \
            np.ones_like(topo.dem)

        # get our effective veg surface roughness
        # to use in log law scaling of WindNinja data
        # using the relationship in
        # https://www.jstage.jst.go.jp/article/jmsj1965/53/1/53_1_96/_pdf
        self.veg_roughness = topo.veg_height / 7.39

        # make sure roughness stays reasonable using bounds from
        # http://www.iawe.org/Proceedings/11ACWE/11ACWE-Cataldo3.pdf
        self.veg_roughness[self.veg_roughness < 0.01] = 0.01
        self.veg_roughness[np.isnan(self.veg_roughness)] = 0.01
        self.veg_roughness[self.veg_roughness > 1.6] = 1.6

        # precalculate scale arrays so we don't do it every timestep
        self.ln_wind_scale = np.log(
            (self.veg_roughness + self.wind_height) / self.veg_roughness
        ) / np.log(
            (self.wn_roughness + self.wind_height) / self.wn_roughness
        )

    def initialize_interp(self, t):
        """Initialize the interpolation weights

        Arguments:
            t {datetime} -- initialize with this file
        """

        # do this first to speedup the interpolation later
        # find vertices and weights to speedup interpolation fro ascii file
        fp_vel = self.wind_ninja_path(t, 'vel')

        # get wind ninja topo stats
        ts2 = utils.get_asc_stats(fp_vel)
        self.windninja_x = ts2['x'][:]
        self.windninja_y = ts2['y'][:]

        XW, YW = np.meshgrid(self.windninja_x, self.windninja_y)
        self.wn_mx = XW.flatten()
        self.wn_my = YW.flatten()

        xy = np.zeros([XW.shape[0]*XW.shape[1], 2])
        xy[:, 1] = self.wn_my
        xy[:, 0] = self.wn_mx
        uv = np.zeros([self.X.shape[0]*self.X.shape[1], 2])
        uv[:, 1] = self.Y.flatten()
        uv[:, 0] = self.X.flatten()

        self.vtx, self.wts = utils.interp_weights(xy, uv, d=2)

        self.init_interp = False

    def distribute(self, data_speed, data_direction):
        """Distribute the wind for the model

        Arguments:
            data_speed {DataFrame} -- wind speed data frame
            data_direction {DataFrame} -- wind direction data frame
        """

        t = data_speed.name

        if self.init_interp:
            self.initialize_interp(t)

        wind_speed, wind_direction = self.convert_wind_ninja(t)
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction

    def convert_wind_ninja(self, t):
        """
        Convert the WindNinja ascii grids back to the SMRF grids and into the
        SMRF data streamself.

        Args:
            t: datetime of timestep

        Returns:
            ws: wind speed numpy array
            wd: wind direction numpy array

        """

        # get the ascii files that need converted
        fp_vel = self.wind_ninja_path(t, 'vel')
        data_vel = np.loadtxt(fp_vel, skiprows=6)
        data_vel_int = data_vel.flatten()

        # interpolate to the SMRF grid from the WindNinja grid
        g_vel = utils.grid_interpolate(
            data_vel_int, self.vtx,
            self.wts, self.X.shape)

        # There will be NaN's around the edge, hanlde those first
        if self.model_dxdy != self.wind_ninja_dxy:
            self._logger.debug('Wind speed from WindNinja has NaN, filling')

            g_vel = self.fill_data(g_vel)

        # log law scale
        g_vel = g_vel * self.ln_wind_scale

        # wind direction from angle, split into u,v components then interpolate
        fp_ang = self.wind_ninja_path(t, 'ang')
        data_ang = np.loadtxt(fp_ang, skiprows=6)

        u = np.sin(data_ang * np.pi / 180)
        v = np.cos(data_ang * np.pi / 180)

        ui = utils.grid_interpolate(
            u.flatten(), self.vtx, self.wts, self.X.shape)
        vi = utils.grid_interpolate(
            v.flatten(), self.vtx, self.wts, self.X.shape)

        uf = self.fill_data(ui)
        vf = self.fill_data(vi)

        g_ang = np.arctan2(uf, vf) * 180 / np.pi
        g_ang[g_ang < 0] = g_ang[g_ang < 0] + 360

        return g_vel, g_ang

    def fill_data(self, g_vel):
        """Fill the WindNinja array that has NaN's.
        This makes an assumption that all the NaN values are along
        the left and bottom edge. This will be the case in the Northern
        hemisphere. First fill the Y direction with 1d interpolation
        exprapolated to the edges, then do the same in the X direction.
        At the end, it will check to ensure that there are no NaN values
        left.

        Arguments:
            g_vel {np.array} -- numpy array to fill

        Raises:
            ValueError: If there are still NaN values after filling

        Returns:
            np.array -- filled numpy array
        """

        ix = np.sum(np.isnan(g_vel[0, :]))
        iy = np.sum(np.isnan(g_vel[:, ix+1]))

        #  first go in the Y direction
        yi = g_vel[:, ix:ix+10]
        xi = self.X[0, ix:ix+10]
        x = self.X[0, :ix]

        o = np.apply_along_axis(interpx, axis=1, arr=yi, xi=xi, x=x)
        g_vel[:, :ix] = o

        #  first go in the X direction
        yi = g_vel[-iy-10:-iy, :]
        xi = self.Y[-iy-10:-iy, 0]
        x = self.Y[-iy:, 0]

        o = np.apply_along_axis(interpx, axis=0, arr=yi, xi=xi, x=x)
        g_vel[-iy:, :] = o

        if np.any(np.isnan(g_vel)):
            raise ValueError('WindNinja data still has NaN values')

        return g_vel
