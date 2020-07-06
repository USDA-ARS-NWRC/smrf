import logging
import os

import pandas as pd


class LoadCSV():

    def __init__(self, *args, **kwargs):

        for keys in kwargs.keys():
            setattr(self, keys, kwargs[keys])

        self._logger = logging.getLogger(__name__)

    def load(self):
        """
        Load the data from a csv file
        Fields that are operated on
        - metadata -> dictionary, one for each station,
        must have at least the following:
        primary_id, X, Y, elevation
        - csv data files -> dictionary, one for each time step,
        must have at least the following columns:
        date_time, column names matching metadata.primary_id
        """

        self._logger.info('Reading data coming from CSV files')

        if self.stations is not None:
            self._logger.debug('Using only stations {0}'.format(
                ", ".join(self.stations)))

        variable_list = list(self.config.keys())
        variable_list.remove('stations')
        df_dict = {}
        for variable in variable_list:
            filename = self.config[variable]

            self._logger.debug('Reading {}...'.format(filename))
            if variable == 'metadata':
                df = pd.read_csv(
                    filename,
                    index_col='primary_id')
                # Ensure all stations are all caps.
                df.index = [s.upper() for s in df.index]

            else:
                df = pd.read_csv(
                    filename,
                    index_col='date_time',
                    parse_dates=[0])
                df = df.tz_localize(self.time_zone)
                df.columns = [s.upper() for s in df.columns]

                # if sta is not None:

                #     data_sta = dp_full.columns.str.upper()

                #     # Grab IDs from user list thats also in Data
                #     self.stations = [s for s in data_sta if s in sta]
                #     dp = dp_full[dp_full.columns[(data_sta).isin(sta)]]

                # else:
                #     dp = dp_full

                # Only get the desired dates
                df = df[self.start_date:self.end_date]

                if df.empty:
                    raise Exception("No CSV data found for {0}"
                                    "".format(variable))

            df_dict[variable] = df

        return df_dict
