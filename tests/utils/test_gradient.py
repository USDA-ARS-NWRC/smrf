import numpy as np

from smrf.utils import gradient

from tests.test_configurations import SMRFTestCase


class TestGradient(SMRFTestCase):

    # with self.dx and self.dy equal to 1, the cardinal direction
    # slope values will be np.pi/4 as one of the differences
    # will be zero
    dx = 1
    dy = 1

    # with self.dx and self.dy equal to 1, the slope of the 45 degree
    # areas will be arctan(sqrt(2))
    slope_val = np.arctan(np.sqrt(2))

    def gen_dem_nw(self, dem_size=10):
        dem = np.tile(range(10), (10, 1)).transpose()

        for i in range(dem_size):
            dem[i, :] = np.arange(i, i+dem_size)
        return dem

    def gen_dem_sw(self, dem_size=10):
        dem = np.tile(range(10), (10, 1)).transpose()

        for i in range(1, 1+dem_size):
            dem[-i, :] = np.arange(i, i+dem_size)
        return dem

    def gen_dem_se(self, dem_size=10):
        dem = np.tile(range(10), (10, 1)).transpose()

        for i in range(1, 1+dem_size):
            dem[-i, :] = np.arange(i+dem_size, i, -1)
        return dem

    def gen_dem_ne(self, dem_size=10):
        dem = np.tile(range(10), (10, 1)).transpose()

        for i in range(dem_size):
            dem[i, :] = np.arange(i+dem_size, i, -1)
        return dem


class TestGradientD4(TestGradient):

    def test_gradient_d4_west(self):
        """ Test for the gradient_d4 for west """

        # test west slope and aspect
        dem = np.tile(range(10), (10, 1))
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 270))
        self.assertTrue(np.all(ipw_a == -np.pi/2))

    def test_gradient_d4_north(self):
        """ Test for the gradient_d4 for north """

        # test north slope and aspect
        dem = np.tile(range(10), (10, 1)).transpose()
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 0))
        self.assertTrue(np.all(np.abs(ipw_a) == np.pi))

    def test_gradient_d4_east(self):
        """ Test for the gradient_d4 for east """

        # test east slope and aspect
        dem = np.fliplr(np.tile(range(10), (10, 1)))
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 90))
        self.assertTrue(np.all(ipw_a == np.pi/2))

    def test_gradient_d4_south(self):
        """ Test for the gradient_d4 for south """

        # test south slope and aspect
        dem = np.flipud(np.tile(range(10), (10, 1)).transpose())
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 180))
        self.assertTrue(np.all(ipw_a == 0))

    def test_gradient_d4_nw(self):
        """ Test for the gradient_d4 for nw """

        # test northwest slope and aspect
        dem = self.gen_dem_nw()
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 315))
        self.assertTrue(np.all(ipw_a == (-np.pi/2 - np.pi/4)))

    def test_gradient_d4_sw(self):
        """ Test for the gradient_d4 for north """

        # test southwest slope and aspect
        dem = self.gen_dem_sw()
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 225))
        self.assertTrue(np.all(ipw_a == -np.pi/4))

    def test_gradient_d4_se(self):
        """ Test for the gradient_d4 for se """

        # test southeast slope and aspect
        dem = self.gen_dem_se()
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 135))
        self.assertTrue(np.all(ipw_a == np.pi/4))

    def test_gradient_d4_ne(self):
        """ Test for the gradient_d4 for ne """

        # test northeast slope and aspect
        dem = self.gen_dem_ne()
        py_slope, asp = gradient.gradient_d4(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 45))
        self.assertTrue(np.all(ipw_a == (np.pi/2 + np.pi/4)))


class TestGradientD8(TestGradient):

    def test_gradient_d8_west(self):
        """ Test for the gradient_d8 for west """

        # test west slope and aspect
        dem = np.tile(range(10), (10, 1))
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 270))
        self.assertTrue(np.all(ipw_a == -np.pi/2))

    def test_gradient_d8_north(self):
        """ Test for the gradient_d8 for north """

        # test north slope and aspect
        dem = np.tile(range(10), (10, 1)).transpose()
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 0))
        self.assertTrue(np.all(np.abs(ipw_a) == np.pi))

    def test_gradient_d8_east(self):
        """ Test for the gradient_d8 for east """

        # test east slope and aspect
        dem = np.fliplr(np.tile(range(10), (10, 1)))
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 90))
        self.assertTrue(np.all(ipw_a == np.pi/2))

    def test_gradient_d8_south(self):
        """ Test for the gradient_d8 for south """

        # test south slope and aspect
        dem = np.flipud(np.tile(range(10), (10, 1)).transpose())
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == np.pi/4))
        self.assertTrue(np.all(asp == 180))
        self.assertTrue(np.all(ipw_a == 0))

    def test_gradient_d8_nw(self):
        """ Test for the gradient_d8 for nw """

        # test northwest slope and aspect
        dem = self.gen_dem_nw()
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 315))
        self.assertTrue(np.all(ipw_a == (-np.pi/2 - np.pi/4)))

    def test_gradient_d8_sw(self):
        """ Test for the gradient_d8 for sw """

        # test southwest slope and aspect
        dem = self.gen_dem_sw()
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 225))
        self.assertTrue(np.all(ipw_a == -np.pi/4))

    def test_gradient_d8_se(self):
        """ Test for the gradient_d8 for se """

        # test southeast slope and aspect
        dem = self.gen_dem_se()
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 135))
        self.assertTrue(np.all(ipw_a == np.pi/4))

    def test_gradient_d8_ne(self):
        """ Test for the gradient_d8 for ne """

        # test northeast slope and aspect
        dem = self.gen_dem_ne()
        py_slope, asp = gradient.gradient_d8(dem, self.dx, self.dy)
        ipw_a = gradient.aspect_to_ipw_radians(asp)

        self.assertTrue(np.all(py_slope == self.slope_val))
        self.assertTrue(np.all(asp == 45))
        self.assertTrue(np.all(ipw_a == (np.pi/2 + np.pi/4)))

    # Used to bulid comparisons for the Pull Request
    # def test_gradient(self):
    #     """ Test the gradient methods """

    #     topo_config = {
    #         'basin_lon': -116.7547,
    #         'basin_lat': 43.067,
    #         'filename': 'tests/RME/topo/topo.nc',
    #         'type': 'netcdf',
    #         'gradient_method': 'gradient_d8'
    #     }

    #     # IPW topo calc
    #     # First converts DEM to ipw 16-bit image
    #     # Gradient output is 8-bit image
    #     topo = loadTopo.topo(topo_config, calcInput=True,
    #                          tempDir='tests/RME/output')

    #     # IPW slope is sin(S)
    #     # ipw_slope = np.arcsin(topo.slope)
    #     ipw_slope = topo.slope
    #     ipw_aspect = topo.aspect

    #     # python calculation
    #     self.dx = np.mean(np.diff(topo.x))
    #     self.dy = np.mean(np.diff(topo.y))

    #     py_slope4, a4 = gradient.gradient_d4(topo.dem, self.dx,
    # self.dy, aspect_rad=True)
    #     py_slope8, a8 = gradient.gradient_d8(topo.dem, self.dx,
    # self.dy, aspect_rad=True)

        # fig, axs = plt.subplots(3, 2)
        # im = axs[0, 0].imshow(180 * (ipw_slope - py_slope4) / np.pi)
        # axs[0, 0].set_title('IPW - Python gradient_d4 [deg]')
        # plt.colorbar(im, ax=axs[0, 0])

        # im = axs[0, 1].imshow(180 * (ipw_aspect - a4) / np.pi)
        # axs[0, 1].set_title('Aspect IPW - Python gradient_d4 [deg]')
        # fig.colorbar(im, ax=axs[0, 1])

        # im = axs[1, 0].imshow(180 * (ipw_slope - py_slope8) / np.pi)
        # axs[1, 0].set_title('IPW - Python gradient_d8 [deg]')
        # fig.colorbar(im, ax=axs[1, 0])

        # im = axs[1, 1].imshow(180 * (ipw_aspect - a8) / np.pi)
        # axs[1, 1].set_title('Aspect IPW - Python gradient_d8 [deg]')
        # fig.colorbar(im, ax=axs[1, 1])

        # im = axs[2, 0].imshow(180 * (py_slope4 - py_slope8) / np.pi)
        # axs[2, 0].set_title(
        #     'Python gradient_d4 - Python gradient_d8 [deg]')
        # fig.colorbar(im, ax=axs[2, 0])

        # im = axs[2, 1].imshow(180 * (a4 - a8) / np.pi)
        # axs[2, 1].set_title(
        #     'Aspect Python gradient_d4 - Python gradient_d8 [deg]')
        # fig.colorbar(im, ax=axs[2, 1])

        # plt.show()

        # fig, axs = plt.subplots(3, 2)
        # im = axs[0, 0].hist(
        #     180 * (ipw_slope - py_slope4).flatten() / np.pi, bins=30)
        # axs[0, 0].set_title('IPW - Python gradient_d4 [deg]')

        # im = axs[0, 1].hist(180 * (ipw_aspect - a4).flatten() /
        # np.pi, bins=30)
        # axs[0, 1].set_title('Aspect IPW - Python gradient_d4 [deg]')

        # im = axs[1, 0].hist(
        #     180 * (ipw_slope - py_slope8).flatten() / np.pi, bins=30)
        # axs[1, 0].set_title('IPW - Python gradient_d8 [deg]')

        # im = axs[1, 1].hist(180 * (ipw_aspect - a8).flatten() /
        # np.pi, bins=30)
        # axs[1, 1].set_title('Aspect IPW - Python gradient_d8 [deg]')

        # im = axs[2, 0].hist(
        #     180 * (py_slope4 - py_slope8).flatten() / np.pi, bins=30)
        # axs[2, 0].set_title(
        #     'Python gradient_d4 - Python gradient_d8 [deg]')

        # im = axs[2, 1].hist(180 * (a4 - a8).flatten() / np.pi, bins=30)
        # axs[2, 1].set_title(
        #     'Aspect Python gradient_d4 - Python gradient_d8 [deg]')

        # plt.show()
