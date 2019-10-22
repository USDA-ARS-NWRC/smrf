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
        # First converts DEM to ipw 16-bit image
        # Gradient output is 8-bit image
        topo = loadTopo.topo(topo_config, calcInput=True,
                             tempDir='tests/RME/output')

        # IPW slope is sin(S)
        ipw_slope = np.arcsin(topo.slope)
        ipw_aspect = topo.aspect

        # python calculation
        dx = np.mean(np.diff(topo.x))
        dy = np.mean(np.diff(topo.y))

        py_slope4, a4 = gradient.gradient_d4(topo.dem, dx, dy)
        py_slope8, a8 = gradient.gradient_d8(topo.dem, dx, dy)

        fig, axs = plt.subplots(3, 2)
        im = axs[0, 0].imshow(180 * (ipw_slope - py_slope4) / np.pi)
        axs[0, 0].set_title('IPW - Python gradient_d4 [deg]')
        plt.colorbar(im, ax=axs[0, 0])

        im = axs[0, 1].imshow(180 * (ipw_aspect - a4) / np.pi)
        axs[0, 1].set_title('Aspect IPW - Python gradient_d4 [deg]')
        fig.colorbar(im, ax=axs[0, 1])

        im = axs[1, 0].imshow(180 * (ipw_slope - py_slope8) / np.pi)
        axs[1, 0].set_title('IPW - Python gradient_d8 [deg]')
        fig.colorbar(im, ax=axs[1, 0])

        im = axs[1, 1].imshow(180 * (ipw_aspect - a8) / np.pi)
        axs[1, 1].set_title('Aspect IPW - Python gradient_d8 [deg]')
        fig.colorbar(im, ax=axs[1, 1])

        im = axs[2, 0].imshow(180 * (py_slope4 - py_slope8) / np.pi)
        axs[2, 0].set_title(
            'Python gradient_d4 - Python gradient_d8 [deg]')
        fig.colorbar(im, ax=axs[2, 0])

        im = axs[2, 1].imshow(180 * (a4 - a8) / np.pi)
        axs[2, 1].set_title(
            'Aspect Python gradient_d4 - Python gradient_d8 [deg]')
        fig.colorbar(im, ax=axs[2, 1])

        plt.show()
