import numpy as np
import matplotlib.pyplot as plt

from smrf.data import loadTopo
from smrf.utils import gradient

from tests.test_configurations import SMRFTestCase


class TestGradient(SMRFTestCase):

    def test_gradient(self):
        """ Test the gradient methods """

        topo_config = {
            'basin_lon': -116.7547,
            'basin_lat': 43.067,
            'filename': 'tests/RME/topo/topo.nc',
            'type': 'netcdf',
            'threading': False
        }

        # IPW topo calc
        topo = loadTopo.topo(topo_config, calcInput=True,
                             tempDir='tests/RME/output')

        # IPW slope is sin(S)
        ipw_slope = np.arcsin(topo.slope)

        # python calculation
        dx = np.mean(np.diff(topo.x))
        dy = np.mean(np.diff(topo.y))

        py_slope = gradient.gradient_d4(topo.dem, dx, dy)

        result = 180 * (ipw_slope - py_slope) / np.pi
        plt.imshow(result)
        plt.colorbar()
        plt.show()
