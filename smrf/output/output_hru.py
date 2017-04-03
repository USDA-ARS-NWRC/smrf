"""
Functions to output the gridded data for a HRU
"""

__version__ = '0.1.1'

import netCDF4 as nc
import numpy as np
from scipy import stats
import logging, os
from datetime import datetime
import pandas as pd

class output_hru():
    
    """
    Class output_hru() to output values to a HRU dataframe, then to a file
    """
    
    fmt = '%Y-%m-%d %H:%M:%S'
    
    def __init__(self, variable_list, topo, date_time, config):
        """
        Initialize the output_hru() class
        
        Args:
            variable_list: list of dicts, one for each variable
            topo: loadTopo instance
            date_time: smrf.date_time, array of dates for the SMRF run
            config: configuration for the output
        """
        
        self._logger = logging.getLogger(__name__)
        self.config = config
        
        # check some defaults based on the output type
        self.prms_flag = False
        if config['output_type'] == 'csv':
            ext = '.csv'
            
        elif config['output_type'] == 'prms':
            ext = '.data'
            self.prms_flag = True
            if not os.path.isfile(self.config['hru_file']):
                raise Exception('HRU file does not exist')
            
            
        # go through the variable list and make full file names
        for v in variable_list:
            variable_list[v]['file_name'] = variable_list[v]['out_location'] + ext
            
        self.variable_list = variable_list
        
        # process the time section
        self.out_frequency = int(config['frequency'])
        self.date_time = date_time
        self.idx = 0
        
        
        # read in the HRU file
        self._logger.debug('Reading HRU ascii {}'.format(self.config['hru_file']))
        
        hru = np.loadtxt(self.config['hru_file'], skiprows=6)
        hru_max = int(np.max(hru))
        self._logger.debug("Number of HRU's: {}".format(hru_max))
        
        self.hru = hru
        self.hru_max = hru_max
        
        IND = {}
        for h in range(hru_max):
            IND[h] = hru == h+1
             
        self.IND = IND
            
        
        # create an empty dataframe
        if self.prms_flag:
            cols = ["year","month","day","hour","minute","second"] + [str(i) for i in range(hru_max)]
            hru_data = pd.DataFrame(index=range(len(self.date_time)), columns=cols)
            
            yrs = np.array([[y.year, y.month, y.day, y.hour, y.minute, y.second] for y in self.date_time])
            hru_data['year'] = yrs[:,0]
            hru_data['month'] = yrs[:,1]
            hru_data['day'] = yrs[:,2]
            hru_data['hour'] = yrs[:,3]
            hru_data['minute'] = yrs[:,4]
            hru_data['second'] = yrs[:,5]
            
            # lets start the output file
            self.generate_prms_header(cols)
            
        else:
            cols = ["date_time"] + [str(i) for i in range(hru_max)]
            hru_data = pd.DataFrame(index=range(len(self.date_time)), columns=cols)
            hru_data['date_time'] = self.date_time
            
        
        self.hru_data = hru_data
   
            
            
        
    def generate_prms_header(self, col_str):
        """
        Generate the header for the PRMS output file
        """
        
        for v in self.variable_list:
            
            with open(self.variable_list[v]['file_name'],'w') as f:
                #Append the PRMS expected Header
                f.write("File Generated using SMRF distributed forcing data\n")
                f.write("{0} {1}\n".format(v, self.hru_max))
                 
                f.write("########################################\n")
                f.close()
        
    
    def output(self, variable, data, date_time):
        """
        Output a time step
        
        Args:
            variable: variable name that will index into variable list
            data: the variable data
            date_time: the date time object for the time step
        """
        
#         hru_data.to_csv(f," ", header = False, index = False)
        
        self._logger.debug('{} Writing variable {} to {} file'.format(date_time, variable, self.config['output_type']))
        
        # determine the location in the output dataframe
        
        
        # loop through the HRU
        for h in range(self.hru_max):
            m_hru = np.nanmean(data[self.IND[h]])
            
            self.hru_data.loc[self.idx, (str(h))] = m_hru
        
        
        with open(self.variable_list[variable]['file_name'], 'a') as f:
            
            row = self.hru_data.iloc[self.idx].to_frame().T
            row.to_csv(f, ' ', header=False, index=False)
            
            f.close()
        
        
        self.idx += 1
        



        
        
        
        
        
        
        
