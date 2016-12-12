"""
Class for running iSnobal

20160107 Scott Havens
"""
__version__ = '0.1.0'

from smrf import ipw
import logging, os
import numpy as np

class isnobal():
    
    def __init__(self, isnobalConfig, topo, tempDir=None):
        """
        Initialize the model run
        - determine if it's a restart or not and create the initial conditions image
        
        Arg:
            isnobalConfig: config file [isnobal] section
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            
        """
        self._logger = logging.getLogger(__name__)
        
        self.config = isnobalConfig
        
        if (tempDir is None) | (tempDir == 'TMPDIR'):
            tempDir = os.environ['TMPDIR']
        self.tempDir = tempDir
        
        # create the initialization image
        self.init_file = os.path.join(self.tempDir, 'init.ipw')
        if self.config['restart']:
            self._logger.debug('Restarting model')
            
        else:
            self._logger.debug('Initializing new model')
            
            s = topo.dem.shape
            z = np.zeros(s)
            
            i = ipw.IPW()
            i.new_band(topo.dem)
            i.new_band(float(self.config['z_0']) * np.ones(s))
            i.new_band(z)
            i.new_band(z)
            i.new_band(z)
            i.new_band(z)
            i.new_band(z)
            i.add_geo_hdr([topo.u, topo.v], [topo.du, topo.dv], topo.units, topo.csys)
            i.write(self.init_file, 16)
            
            
    def runModel(self):
        """
        Run iSnobal
        """
        
        
            
            
