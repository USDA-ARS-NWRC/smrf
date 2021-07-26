from collections import OrderedDict

import numpy as np

import smrf


class MockTopo(smrf.data.load_topo.Topo):
    topoConfig = OrderedDict([('filename', './mock/topo.nc'),
                              ('gradient_method', 'gradient_d8'), ('sky_view_factor_angles', 72),
                              ('northern_hemisphere', True)])
    dem = np.array([[2094., 2092., 2086., 2090.], [2094., 2089., 2091., 2092.], [2094., 2092., 2092., 2096.],
                    [2090., 2089., 2094., 2095.]])
    mask = np.array([[0., 0., 0., 0.], [0., 0., 0., 0.], [0., 0., 0., 0.], [0., 0., 0., 0.]])
    veg_type = np.array(
        [[3126, 3145, 3145, 3145], [3145, 3145, 3145, 3126], [3124, 3145, 3145, 3011], [3124, 3124, 3145, 3011]])
    veg_height = np.array([[2., 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.75], [0.25, 0.25, 0.25, 17.5, ],
                          [0.25, 0.25, 0.25, 7.5, ]])
    veg_k = np.array([[0., 0., 0., 0., ], [0., 0., 0., 0., ], [0., 0., 0., 0.025], [0., 0., 0., 0.025]])
    veg_tau = np.array([[0., 0., 0., 0.], [0., 0., 0., 0.], [0., 0., 0., 0.44], [0., 0., 0., 0.44]])
    nx = 4
    ny = 4
    x = np.array([519675., 519725., 519775., 519825.])
    y = np.array([4767655., 4767705., 4767755., 4767805.])
    X = np.array([[519675., 519725., 519775., 519825.], [519675., 519725., 519775., 519825.],
                  [519675., 519725., 519775., 519825.], [519675., 519725., 519775., 519825.]])
    Y = np.array([[4767655., 4767655., 4767655., 4767655.], [4767705., 4767705., 4767705., 4767705.],
                  [4767755., 4767755., 4767755., 4767755.], [4767805., 4767805., 4767805., 4767805.]])
    dx = 50.0
    dy = 50.0
    cx = 520033.72
    cy = 4768035.0
    northern_hemisphere = True
    zone_number = 11
    basin_lat = 43.06475372378507
    basin_long = -116.75395420397061
    slope_radians = np.array(
        [[0.03997869, 0.07998509, 0.04920454, 0.11829376], [0.069886, 0.04269406, 0.04920454, 0.06935082],
        [0.06394395, 0.00790553, 0.04805144, 0.0180258, ], [0.07485985, 0.03498572, 0.0226346, 0.07275824]])
    sin_slope = np.array(
        [[0.03996804, 0.07989983, 0.04918469, 0.11801806], [0.06982913, 0.04268109, 0.04918469, 0.06929525],
         [0.06390038, 0.00790545, 0.04803295, 0.01802483], [0.07478995, 0.03497858, 0.02263266, 0.07269406]])
    aspect = np.array(
        [[1.57079633, 1.50837752, 2.72336832, -1.95911504], [1.57079633, 1.929567, -2.72336832, -2.09887078],
        [0.89605538, 1.24904577, -2.05769556, -2.15879893], [2.49809154, 3.14159265, -1.46013911, 0.5404195, ]])
    sky_view_factor = np.array(
        [[0.99884509, 0.99658484, 0.99522715, 0.99487732], [0.99692021, 0.99578673, 0.99836789, 0.99727945],
         [0.99684979, 0.99885306, 0.9985448, 0.99970225], [0.99146192, 0.99218187, 0.99925098, 0.99724846]])
    terrain_config_factor = np.array(
        [[0.00075539, 0.00181661, 0.0041677, 0.00162841], [0.00185927, 0.00375765, 0.00102696, 0.00151865],
         [0.00212835, 0.00113132, 0.00087807, 0.00021652], [0.00713773, 0.00751216, 0.00062095, 0.00142868]])
    IMAGES = ['dem', 'mask', 'veg_type', 'veg_height', 'veg_k', 'veg_tau']


class SmrfMocks(object):
    def mock_load_topo(self):
        self.topo = MockTopo
