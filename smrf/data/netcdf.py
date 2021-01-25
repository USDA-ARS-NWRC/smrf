import netCDF4 as nc
import numpy as np
import pandas as pd

from smrf.data.gridded_input import GriddedInput
from smrf.utils.utils import apply_utm


def metadata_name_from_index(index):
    return 'grid_y{:d}_x{:d}'.format(index[0], index[1])


class InputNetcdf(GriddedInput):

    DATA_TYPE = 'netcdf'

    VARIABLES = [
        'air_temp',
        'vapor_pressure',
        'precip',
        'wind_speed',
        'wind_direction',
        'cloud_factor'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.variables = list(self.config.keys())
        self.variables.remove('data_type')
        self.variables.remove('netcdf_file')

    def load(self):
        """
        Load the data from a generic netcdf file
        """

        self._logger.info('Reading data coming from netcdf: {}'.format(
            self.config['netcdf_file'])
        )

        f = nc.Dataset(self.config['netcdf_file'], 'r')

        mlat = f.variables['lat'][:]
        mlon = f.variables['lon'][:]
        mhgt = f.variables['elev'][:]

        if mlat.ndim != 2 & mlon.ndim != 2:
            [mlon, mlat] = np.meshgrid(mlon, mlat)

        # get the values that are in the modeling domain
        ind = (mlat >= self.bbox[1]) & \
            (mlat <= self.bbox[3]) & \
            (mlon >= self.bbox[0]) & \
            (mlon <= self.bbox[2])

        mlat = mlat[ind]
        mlon = mlon[ind]
        mhgt = mhgt[ind]

        # create some fake station names based on the index
        a = np.argwhere(ind)
        primary_id = [metadata_name_from_index(i) for i in a]
        self._logger.debug('{} grid cells within model domain'.format(len(a)))

        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=primary_id,
                                columns=('X', 'Y', 'latitude',
                                         'longitude', 'elevation'))

        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm,
                                  args=(self.topo.zone_number,),
                                  axis=1)

        self.metadata = metadata

        t = f.variables['time']
        time = nc.num2date(t[:].astype(int), t.getncattr(
            'units'), t.getncattr('calendar'))
        # Drop milliseconds and prepare to use as pandas DataFrame index
        time = pd.DatetimeIndex(
            [str(tm.replace(microsecond=0)) for tm in time], tz=self.time_zone
        )

        for variable in self.VARIABLES:
            v_file = self.config[variable]
            self._logger.debug(
                'Loading variable {} from netcdf field {}'.format(
                    variable, v_file)
            )

            df = pd.DataFrame(index=time, columns=primary_id)
            for i in a:
                g = metadata_name_from_index(i)
                df[g] = f.variables[v_file][:, i[0], i[1]]

            # deal with any fillValues
            try:
                fv = f.variables[v_file].getncattr('_FillValue')
                df.replace(fv, np.nan, inplace=True)
            except Exception:
                pass

            # Set variable and subset by start and end time
            setattr(self, variable, df)

        f.close()
