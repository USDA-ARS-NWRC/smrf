import logging
import glob
import os

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

        self.smrf_config = smrf_config
        self.getConfig(smrf_config['wind'])
        self.distribute_drifts = distribute_drifts

        self._logger.debug('Creating the WindNinjaModel')

    def initialize(self, topo, data):
        """Initialize the model with data

        Arguments:
            topo {topo class} -- Topo class
            data {data object} -- SMRF data object
        """

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
