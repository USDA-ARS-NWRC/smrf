from copy import deepcopy
from inicheck.tools import get_user_config, check_config, cast_all_variables

from smrf.framework.model_framework import run_smrf
from .test_configurations import SMRFTestCase


class TestSpatialMethods(SMRFTestCase):
    
    def test_station_spatial_config(self):
        """
        Test the config for different spatial methods
        """
        
        config = deepcopy(self.base_config)
        
        
        config.cfg['air_temp']['distribution'] = 'dk'
        config.cfg['precip']['distribution'] = 'idw'
        
        # kriging doesn't work with 2 stations, so this will fail
        config.cfg['vapor_pressure']['distribution'] = 'kriging'
        config.cfg['vapor_pressure']['nlags'] = 1
        config.cfg['system']['threading'] = False
        
        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)
        
        # test the base run with the config file
        result = run_smrf(config)
        self.assertFalse(result)
        
    
#     def test_grid_config(self):
#         """
#         Test the config for the grid
#         """
#         
#         config = deepcopy(self.base_config)
#         
#         
#         config.cfg['air_temp']['distribution'] = 'grid'
#         config.cfg['precip']['distribution'] = 'idw'
#                 
#         # apply the new recipies
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#         
#         # test the base run with the config file
#         result = run_smrf(config)
#         self.assertTrue(result)