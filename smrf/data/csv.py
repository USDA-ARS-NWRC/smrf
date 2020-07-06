import logging

import pandas as pd

from smrf.utils.utils import check_station_colocation


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

                if self.stations is not None:
                    df = df[df.columns[(df.columns).isin(self.stations)]]

                # Only get the desired dates
                df = df[self.start_date:self.end_date]

                if df.empty:
                    raise Exception("No CSV data found for {0}"
                                    "".format(variable))

            setattr(self, variable, df)

    def check_colocation(self):
        # Check all sections for stations that are colocated
        colocated = check_station_colocation(metadata=self.metadata)
        if colocated is not None:
            self._logger.error(
                "Stations are colocated: {}".format(','.join(colocated[0])))
