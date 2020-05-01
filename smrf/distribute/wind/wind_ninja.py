import logging
import glob
import os

import pytz
import numpy as np
import pandas as pd

from smrf.distribute import image_data
from smrf.utils import utils


class WindNinjaModel(image_data.image_data):

    variable = 'wind'

    def __init__(self, smrf_config, distribute_drifts):
        """Initialize the WinstralWindModel

        Arguments:
            smrf_config {UserConfig} -- entire smrf config
            distribute_drifts {bool} -- distribute drifts if true

        Raises:
            IOError: if maxus file does not match topo size
        """

        image_data.image_data.__init__(self, self.variable)

        self._logger = logging.getLogger(__name__)
        self._logger.debug('Creating the WindNinjaModel')

        self.smrf_config = smrf_config
        self.getConfig(smrf_config['wind'])
        self.distribute_drifts = distribute_drifts

        # wind ninja parameters
        self.wind_ninja_dir = self.config['wind_ninja_dir']
        self.wind_ninja_dxy = self.config['wind_ninja_dxdy']
        self.wind_ninja_pref = self.config['wind_ninja_pref']
        if self.config['wind_ninja_tz'] is not None:
            self.wind_ninja_tz = pytz.timezone(
                self.config['wind_ninja_tz'].title())

        self.start_date = pd.to_datetime(
            self.smrf_config['time']['start_date'])
        self.grid_data = self.smrf_config['gridded']['data_type']

    def initialize(self, topo, data=None):
        """Initialize the model with data

        Arguments:
            topo {topo class} -- Topo class
            data {None} -- Not used but needs to be there
        """

        # meshgrid points
        self.X = topo.X
        self.Y = topo.Y

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
        self.ln_wind_scale = np.log((self.veg_roughness + self.wind_height) / self.veg_roughness) / \
            np.log((self.wn_roughness + self.wind_height) / self.wn_roughness)

        # do this first to speedup the interpolation later #
        # find vertices and weights to speedup interpolation fro ascii file
        fmt_d = '%Y%m%d'
        fp_vel = glob.glob(os.path.join(self.wind_ninja_dir,
                                        'data{}'.format(
                                            self.start_date.strftime(fmt_d)),
                                        'wind_ninja_data',
                                        '*{}m_vel.asc'.format(self.wind_ninja_dxy)))[0]

        # get wind ninja topo stats
        ts2 = utils.get_asc_stats(fp_vel)
        self.windninja_x = ts2['x'][:]
        self.windninja_y = ts2['y'][:]

        XW, YW = np.meshgrid(self.windninja_x, self.windninja_y)
        xwint = XW.flatten()
        ywint = YW.flatten()
        self.wn_mx = xwint
        self.wn_my = ywint

        xy = np.zeros([XW.shape[0]*XW.shape[1], 2])
        xy[:, 1] = ywint
        xy[:, 0] = xwint
        uv = np.zeros([self.X.shape[0]*self.X.shape[1], 2])
        uv[:, 1] = self.Y.flatten()
        uv[:, 0] = self.X.flatten()

        self.vtx, self.wts = utils.interp_weights(xy, uv, d=2)

    def distribute(self, data_speed, data_direction):
        """Distribute the wind for the model

        Arguments:
            data_speed {DataFrame} -- wind speed data frame
            data_direction {DataFrame} -- wind direction data frame
        """

        wind_speed, wind_direction = self.convert_wind_ninja(t)
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction

    def convert_wind_ninja(self, t):
        """
        Convert the WindNinja ascii grids back to the SMRF grids and into the
        SMRF data streamself.

        Args:
            t:              datetime of timestep

        Returns:
            ws: wind speed numpy array
            wd: wind direction numpy array

        """
        # fmt_wn = '%Y-%m-%d_%H%M'
        fmt_wn = '%m-%d-%Y_%H%M'
        fmt_d = '%Y%m%d'

        # get the ascii files that need converted
        # file example tuol_09-20-2018_1900_200m_vel.prj
        # find timestamp of WindNinja file
        t_file = t.astimezone(self.wind_ninja_tz)

        fp_vel = os.path.join(self.wind_ninja_dir,
                              'data{}'.format(t.strftime(fmt_d)),
                              'wind_ninja_data',
                              '{}_{}_{:d}m_vel.asc'.format(self.wind_ninja_pref,
                                                           t_file.strftime(
                                                               fmt_wn),
                                                           self.wind_ninja_dxy))

        # make sure files exist
        if not os.path.isfile(fp_vel):
            raise ValueError(
                '{} in windninja convert module does not exist!'.format(fp_vel))

        data_vel = np.loadtxt(fp_vel, skiprows=6)
        data_vel_int = data_vel.flatten()

        # interpolate to the SMRF grid from the WindNinja grid
        g_vel = utils.grid_interpolate(data_vel_int, self.vtx,
                                       self.wts, self.X.shape)

        # flip because it comes out upsidedown
        g_vel = np.flipud(g_vel)
        # log law scale
        g_vel = g_vel * self.ln_wind_scale

        # Don't get angle if not distributing drifts
        if self.distribute_drifts:
            fp_ang = os.path.join(self.wind_ninja_dir,
                                  'data{}'.format(t.strftime(fmt_d)),
                                  'wind_ninja_data',
                                  '{}_{}_{:d}m_ang.asc'.format(self.wind_ninja_pref,
                                                               t_file.strftime(
                                                                   fmt_wn),
                                                               self.wind_ninja_dxy))

            if not os.path.isfile(fp_ang):
                raise ValueError(
                    '{} in windninja convert module does not exist!'.format(fp_ang))

            data_ang = np.loadtxt(fp_ang, skiprows=6)
            data_ang_int = data_ang.flatten()

            g_ang = utils.grid_interpolate(data_ang_int, self.vtx,
                                           self.wts, self.X.shape)

            g_ang = np.flipud(g_ang)

        else:
            g_ang = None

        return g_vel, g_ang
