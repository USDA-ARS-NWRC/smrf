"""
Distribute thermal long wave using only 1 method

20170731 Micah Sandusky
"""

import smrf
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import netCDF4 as nc
from smrf.envphys import radiation
import pytz


def main():

    # read config file
    # create a new model instance
    # initialize the model
    # run the model
    # output if necessary

    #try:
        start = datetime.now()

        configFile = '../test_data/testConfig.ini'
        if len(sys.argv) > 1:
            configFile = sys.argv[1]

        # read in air temp and vapor pressure
        # fp_airtemp = '/data/...'
        # fp_vaporpressure = '/data/...'
        # fp_dewpoint = '/data/...'
        # ta_file = nc.Dataset(fp_airtemp, 'r')
        # ea_file = nc.Dataset(fp_vaporpressure, 'r')
        # dp_file = nc.Dataset(fp_dewpoint, 'r')
        # ea_var = 'vapor_pressure'
        # ta_var = 'air_temp'
        # dp_var = 'dew_point'

        # initialize
        with smrf.framework.SMRF(configFile) as s:
            # load topo data
            s.loadTopo(calcInput=True)

            # # Create the distribution class
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
                cosz, azimuth = radiation.sunang(t.astimezone(pytz.utc),
                                             s.topo.topoConfig['basin_lat'],
                                             s.topo.topoConfig['basin_lon'],
                                             zone=0,
                                             slope=0,
                                             aspect=0)
                illum_ang = None
                if cosz > 0:
                    illum_ang = radiation.shade(s.topo.slope,
                                            s.topo.aspect,
                                            azimuth,
                                            cosz)

                # find variable at the timestep
                # ea_step = ea_file.variables[ea_var][output_count,:]
                # ta_step = ta_file.variables[ta_var][output_count,:]
                # dp_step = dp_file.variables[dp_var][output_count,:]

                s.distribute['solar']._distribute(s.data.cloud_factor.ix[t], other_attribute='cloud_factor')

                # create zero albedo field
                if s.distribute['solar'].config['correct_albedo']:
                    pass
                else:
                    albedo = np.zeros_like(s.topo.slope)
                    zero_storm_day = 0.0

                ea_step = np.ones_like(albedo)
                ta_step = np.ones_like(albedo)
                dp_step = np.ones_like(albedo)

                s.distribute['solar'].distribute(s.data.cloud_factor.ix[t], illum_ang, cosz,
                                                azimuth, zero_storm_day,
                                                albedo,
                                                albedo)

                s.distribute['thermal'].distribute(t, ta_step,
                                                   ea_step,
                                                   dp_step,
                                                   s.distribute['solar'].cloud_factor)

                # output at the frequency and the last time step
                if (output_count % s.config['output']['frequency'] == 0) or (output_count == len(s.date_time)):
                    s.output(t)

            # ta_file.close()
            # ea_file.close()
            # dp_file.close()

            s._logger.info(datetime.now() - start)

    # except Exception as e:
    #     s._logger.error(e)


if __name__ == '__main__':
    main()
