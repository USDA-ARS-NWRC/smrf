"""
Distribute thermal long wave using only 1 method

20170731 Micah Sandusky
"""

import smrf
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime


def main():

    # read config file
    # create a new model instance
    # initialize the model
    # run the model
    # output if necessary

    try:
        start = datetime.now()
        
        configFile = '../test_data/testConfig.ini'
        if len(sys.argv) > 1:
            configFile = sys.argv[1]

        # initialize
        with smrf.framework.SMRF(configFile) as s:
            # load topo data
            s.loadTopo(calcInput=True)

            # Create the distribution class
            s.distribute['air_temp'] = smrf.distribute.air_temp.ta(s.config['air_temp'])
            s.distribute['vapor_pressure'] = smrf.distribute.vapor_pressure.vp(s.config['vapor_pressure'])
            s.distribute['albedo'] = smrf.distribute.albedo.albedo(s.config['albedo'])
            s.distribute['solar'] = smrf.distribute.solar.solar(s.config['solar'],
                                                                s.distribute['albedo'].config,
                                                                s.topo.stoporad_in_file,
                                                                s.config['system']['temp_dir'])
            s.distribute['thermal'] = smrf.distribute.thermal.th(s.config['thermal'])

            # load weather data  and station metadata
            s.loadData()

            # Initialize the distibution
            for v in s.distribute:
                s.distribute[v].initialize(s.topo, s.data)

            s.initializeOutput()

            # 7. Distribute the data
            for output_count,t in enumerate(s.date_time):

                s.distribute['air_temp'].distribute(s.data.air_temp.ix[t])
                s.distribute['solar']._distribute(s.data.cloud_factor.ix[t], other_attribute='cloud_factor')
                s.distribute['vapor_pressure'].distribute(s.data.vapor_pressure.ix[t],
                                                          s.distribute['air_temp'].air_temp)
                s.distribute['thermal'].distribute(t, s.distribute['air_temp'].air_temp,
                                                   s.distribute['vapor_pressure'].vapor_pressure,
                                                   s.distribute['vapor_pressure'].dew_point,
                                                   s.distribute['solar'].cloud_factor)

                # output at the frequency and the last time step
                if (output_count % s.config['output']['frequency'] == 0) or (output_count == len(s.date_time)):
                    s.output(t)

            s._logger.info(datetime.now() - start)

    except Exception as e:
        s._logger.error(e)


if __name__ == '__main__':
    main()
