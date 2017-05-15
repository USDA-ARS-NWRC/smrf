"""
There are many different options for correcting clear sky thermal (long wave) radiation for clouds in
SMRF. Currently 4 methods are available and this example will show the differences between
the methods.

20170515 Scott Havens
"""

import smrf
import sys
import matplotlib.pyplot as plt
import numpy as np


# the different methods that can be used, the Marks1979 will be used for 
# the base comparison of clear sky thermal radiation
methods = ['Garen2005', 'Unsworth1975', 'Kimball1982', 'Crawford1999']


def main():
        
    # read config file
    # create a new model instance
    # initialize the model
    # run the model
    # output if necessary
    
    try:
        configFile = '../test_data/testConfig.ini'
        if len(sys.argv) > 1:
            configFile = sys.argv[1]
        
        # initialize
        s = smrf.framework.SMRF(configFile)
        
        # load topo data
        s.loadTopo(calcInput=True)
        
        # Create the distribution class
        s.distribute['air_temp'] = smrf.distribute.air_temp.ta(s.config['air_temp'])
        s.distribute['vapor_pressure'] = smrf.distribute.vapor_pressure.vp(s.config['vapor_pressure'])
        s.distribute['thermal'] = smrf.distribute.thermal.th(s.config['thermal'])
        s.distribute['albedo'] = smrf.distribute.albedo.albedo(s.config['albedo'])
        s.distribute['solar'] = smrf.distribute.solar.solar(s.config['solar'],
                                                            s.distribute['albedo'].config,
                                                            s.topo.stoporad_in_file,
                                                            s.config['system']['temp_dir'])
        
        # load weather data  and station metadata
        s.loadData()
        
        # Initialize the distibution
        for v in s.distribute:
            s.distribute[v].initialize(s.topo, s.data.metadata)
            
        # Distribute the data for a single timestep
        t = s.date_time[0]
        s.distribute['air_temp'].distribute(s.data.air_temp.ix[t])
        s.distribute['solar']._distribute(s.data.cloud_factor.ix[t], other_attribute='cloud_factor')
        s.distribute['vapor_pressure'].distribute(s.data.vapor_pressure.ix[t],
                                                  s.distribute['air_temp'].air_temp)
        
        
        # calculate the long wave for different methods
        s.distribute['thermal'].correct_cloud = True
        s.distribute['thermal'].correct_veg = False
        
        # create some plots
        fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(12,8))
        fig.tight_layout()
        fig.subplots_adjust(left=0.1)
        fig.subplots_adjust(right=0.9)
        
        for i,m in enumerate(methods):
            idx = np.unravel_index(i,ax.shape)
            
            s.distribute['thermal'].cloud_method = m
        
            s.distribute['thermal'].distribute(t, s.distribute['air_temp'].air_temp,
                                              s.distribute['vapor_pressure'].vapor_pressure,
                                              s.distribute['vapor_pressure'].dew_point,
                                              s.distribute['solar'].cloud_factor)
            
            if m == 'Garen2005':
                D = s.distribute['thermal'].thermal
                im = ax[idx].imshow(D, cmap='viridis')
                
                cbar_ax = fig.add_axes([0.05, 0.15, 0.01, 0.7])
                fig.colorbar(im, cax=cbar_ax)
                
            else:
                d = D - s.distribute['thermal'].thermal
                im = ax[idx].imshow(d, cmap='coolwarm', vmin=-100, vmax=50)
                
                if i == 3:
                    cbar_ax = fig.add_axes([0.95, 0.15, 0.01, 0.7])
                    fig.colorbar(im, cax=cbar_ax)
            

            ax[idx].set_aspect('equal')
            ax[idx].autoscale(tight=True)
            ax[idx].axes.get_xaxis().set_visible(False)
            ax[idx].axes.get_yaxis().set_visible(False)
            ax[idx].set_title(m)
            
            
        plt.show()
        
        
      
        
    except Exception as e:
        s._logger.error(e)
        
if __name__ == '__main__':
    main()

    
    
    
    
    