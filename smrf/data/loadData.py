from smrf.data import mysql_data
import logging
import pandas as pd

class wxdata():
    """
    Class for loading and storing the data, either from
    - CSV file
    - MySQL database
    - Add other sources here

    Inputs to data() are:
    - dataConfig, either the [csv] or [mysql] section
    - start_date, datetime object
    - end_date, datetime object
    - dataType, either 'csv' or 'mysql'

    The data will be loaded into a Pandas dataframe

    """

    variables = ['air_temp',
                 'vapor_pressure',
                 'precip',
                 'wind_speed',
                 'wind_direction',
                 'cloud_factor']
    db_config_vars = ['user',
                      'password',
                      'host',
                      'database',
                      'port',
                      'metadata',
                      'data_table',
                      'station_table']

    def __init__(self, dataConfig, start_date, end_date, time_zone='UTC',
                 stations=None, dataType=None):

        if dataType is None:
            raise Exception('''loadData.data() must have a specified dataType
                            of "csv" or "mysql"''')

        self.dataConfig = dataConfig
        self.dataType = dataType
        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = time_zone
        self.stations = stations

        self._logger = logging.getLogger(__name__)

        # load the data
        if dataType == 'csv':
            self.load_from_csv()

        elif dataType == 'mysql':
            self.load_from_mysql()
        else:
            raise Exception('Could not resolve dataType')

        # correct for the timezone
        for v in self.variables:
            if hasattr(self, v):
                d = getattr(self, v)
                setattr(self, v, d.tz_localize(tz=self.time_zone))

    def load_from_csv(self):
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
            if 'stations' in self.stations:
                sta = [s.upper() for s in self.stations['stations']]
                self._logger.debug('Using only stations {0}'.format(
                    self.stations['stations']
                    ))

        # load the data
        v = list(self.variables)
        v.append('metadata')
        for i in v:
            if i in self.dataConfig:

                self._logger.debug('Reading %s...' % self.dataConfig[i])
                if i == 'metadata':
                    dp_final = pd.read_csv(self.dataConfig[i],
                                     index_col='primary_id')
                    #Ensure all stations are all caps.
                    dp_final.index = [s.upper() for s in dp_final.index]

                elif self.dataConfig[i]:
                    dp_full = pd.read_csv(self.dataConfig[i],
                                     index_col='date_time',
                                     parse_dates=[0])
                    dp_full.columns = [s.upper() for s in dp_full.columns]

                    # check to see if pandas read in the date time correctly
                    if not isinstance(dp_full.index[0], pd.Timestamp):
                        raise Exception('''Pandas could not convert
                                        date_time to timestamp.
                                        Try using %Y-%m-%d %H:%M:%S format''')

                    if sta is not None:
                        self.stations = [s for s in dp_full.columns.str.upper() if s in sta]
                        dp = dp_full[dp_full.columns[(dp_full.columns.str.upper()).isin(sta)]]
                    else:
                        dp = dp_full
                    # only get the desired dates
                    dp_final = dp[self.start_date:self.end_date]

                    if dp_final.empty:
                        if self.start_date not in dp_final.index:
                            raise Exception("start_date in config file is not "
                                            "inside of available date range "
                                            "\n{0} not w/in {1} and {2}"
                                            "".format(self.start_date,
                                                      dp.index[0],
                                                      dp.index[-1]))

                        elif self.end_date not in dp_final.index:
                            raise Exception("end_date in config file is not "
                                            "inside of available date range "
                                            "\n{0} not w/in {1} and {2}"
                                            "".format(self.start_date,
                                                      dp.index[0],
                                                      dp.index[-1]))
                        else:
                            raise Exception("No CSV data found for {0}"
                                            "".format(i))

                setattr(self, i, dp_final)

        # check that metadata is there
        try:
            self.metadata
        except:
            raise AttributeError('Metadata missing from configuration file')

    def load_from_mysql(self):
        """
        Load the data from a mysql database
        """

        self._logger.info('Reading data from MySQL database')

        # open the database connection
        data = mysql_data.database(self.dataConfig['user'],
                                   self.dataConfig['password'],
                                   self.dataConfig['host'],
                                   self.dataConfig['database'],
                                   self.dataConfig['port'])

        # ---------------------------------------------------
        # determine if it's stations or client
        sta = None
        if 'stations' in self.stations:
            sta = self.stations['stations']

        c = None
        stable = None
        if 'client' in self.stations:
            c = self.stations['client']
            stable = self.dataConfig['station_table']

        # determine what table for the metadata
        mtable = self.dataConfig['metadata']

        if (sta is None) & (c is None):
            raise Exception('''Error in configuration file for [mysql],
                            must specify either "stations" or "client"''')
        self._logger.debug('Loading metadata from table %s' % mtable)

        # ---------------------------------------------------
        # load the metadata
        self.metadata = data.metadata(mtable, station_ids=sta,
                                      client=c, station_table=stable)

        self._logger.debug('%i stations loaded' % self.metadata.shape[0])

        # ---------------------------------------------------
        # get a list of the stations
        station_ids = self.metadata.index.tolist()
        # get the correct column names if specified, along with variable names
        db_var_names = [val for key, val in self.dataConfig.items()
                        if key not in self.db_config_vars]
        variables = [x for x in self.dataConfig.keys()
                     if x not in self.db_config_vars]

        # get the data
        dp = data.get_data(self.dataConfig['data_table'], station_ids,
                           self.start_date, self.end_date, db_var_names)

        # go through and extract the data
        for v in variables:
            setattr(self, v, dp[self.dataConfig[v]])
