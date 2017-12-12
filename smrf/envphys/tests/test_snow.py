import unittest

import numpy as np
from smrf.envphys.snow import calc_phase_and_density

class NASDETest(unittest.TestCase):
    def test(self):
    	t = np.array([-10])
    	p = np.array([100])
    	snow_rho, perc_snow = calc_phase_and_density(t,p,'marks2017')
        self.assertEqual(round(snow_rho[0]),79)

if __name__ == "__main__":
   unittest.main()
