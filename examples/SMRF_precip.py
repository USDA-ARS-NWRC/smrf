'''
20170330 Scott Havens

Distribute the gridded forcing data to the DEM
'''


import sys
from datetime import datetime

import smrf


def main():

    start = datetime.now()


    configFile = '../test_data/testConfig.ini'
    if len(sys.argv) > 1:
        configFile = sys.argv[1]

    with smrf.framework.SMRF(configFile) as s:

        #===============================================================================
        # Model setup and initialize
        #===============================================================================
        #
        # These are steps that will load the necessary data and initialize the framework
        # Once loaded, this shouldn't need to be re-ran except if something major changes

        # load topo data
        s.loadTopo(calcInput=False)

        # Create the distribution class
        s.distribute['air_temp'] = smrf.distribute.air_temp.ta(s.config['air_temp'])
        s.distribute['vapor_pressure'] = smrf.distribute.vapor_pressure.vp(s.config['vapor_pressure'])
        # print(s.distribute['vapor_pressure'].config['tolerance'])

        s.distribute['wind'] = smrf.distribute.wind.wind(s.config['wind'])
        s.distribute['precip'] = smrf.distribute.precipitation.ppt(s.config['precip'], s.config['time']['time_step'])

        # load weather data  and station metadata
        s.loadData()

        # Initialize the distibution
        for v in s.distribute:
            s.distribute[v].initialize(s.topo, s.data)

        # initialize the outputs if desired
        s.initializeOutput()

        # 7. Distribute the data
        for output_count,t in enumerate(s.date_time):

            s.distribute['air_temp'].distribute(s.data.air_temp.ix[t])

            s.distribute['vapor_pressure'].distribute(s.data.vapor_pressure.ix[t],
                                                    s.distribute['air_temp'].air_temp)

            s.distribute['wind'].distribute(s.data.wind_speed.ix[t],
                                               s.data.wind_direction.ix[t])

            s.distribute['precip'].distribute(s.data.precip.ix[t],
                                              s.distribute['vapor_pressure'].dew_point,
                                              t,
                                              s.data.wind_speed.ix[t],
                                              s.data.air_temp.ix[t],
                                              s.topo.mask)

            # output at the frequency and the last time step
            if (output_count % s.config['output']['frequency'] == 0) or (output_count == len(s.date_time)):
                s.output(t)

    s._logger.info(datetime.now() - start)

if __name__ == '__main__':
    main()
