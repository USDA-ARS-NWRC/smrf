"""
Created on Dec 22, 2015

Read in metadata and data from a MySQL database
The table columns will most likely be hardcoded for ease
of development and users will require the specific table setup
"""

import logging
from datetime import timedelta

import mysql.connector
import numpy as np
import pandas as pd
from scipy import stats as stats


class database:
    """
    Database class for querying metadata and station data
    """

    def __init__(self, user, password, host, db, port):

        try:
            cnx = mysql.connector.connect(user=user,
                                          password=password,
                                          host=host,
                                          database=db,
                                          port=port)

        except mysql.connector.Error as err:
            if err.errno == 1045:  # errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error('Something is wrong with your user name or '
                              ' password')
            elif err.errno == 1049:  # errorcode.ER_BAD_DB_ERROR:
                logging.error('Database does not exist')
            else:
                logging.error(err)

            raise err

        self._db_connection = cnx
        self._db_cur = self._db_connection.cursor()
        self._logger = logging.getLogger(__name__)
        self._logger.info('Connected to MySQL database')

    def metadata(self, table, station_ids=None,
                 client=None, station_table=None):
        """
        Similar to the CorrectWxData database call
        Get the metadata from the database for either the specified stations
        or for the specific group of stations in client

        Args:
            table: metadata table in the database
            station_id: list of stations to read, default None
            client: client to read from the station_table, default None
            station_table: table name that contains the clients and
                list of stations, default None
        Returns:
            d: Pandas DataFrame of station information
        """

        # form the query for getting metadata
        if station_ids is not None:
            qry = "SELECT * FROM {0} WHERE primary_id IN ('{1}')".format(
                table, "','".join(station_ids))

        else:
            qry = """SELECT {0}.* FROM {0} INNER JOIN {1} ON
                    {0}.id={1}.metadata_id WHERE {1}.client='{2}'""".format(
                table, station_table, client)

        self._logger.debug(qry)

        # Execute the query
        d = pd.read_sql(qry, self._db_connection, index_col='primary_id')

        if d.empty:
            raise Exception('No metadata found for query')

        return d

    def get_data(self, table, station_ids, start_date, end_date, variables,
                 time_zone='UTC'):
        """
        Get data from the database, either for the specified stations
        or for the specific group of stations in client

        Args:
            table: table to load data from
            station_ids: list of station ids to get
            start_date: start of time period
            end_date: end of time period
            variable: string for variable to get
            time_zone: String timezone to set the data in
        """
        if isinstance(variables, list):
            variables = ','.join(variables)

        sta = "','".join(station_ids)

        qry = """SELECT date_time,station_id,{0} FROM {1}
             WHERE date_time BETWEEN '{2}' AND '{3}' AND
             station_id IN ('{4}') ORDER BY date_time ASC""".format(
            variables, table, start_date, end_date, sta)

        self._logger.debug(qry)

        # loads all the data
        d = pd.read_sql(qry, self._db_connection, index_col='date_time')
        if d.empty:
            raise Exception('No data found in database')

        # Fill returned values 'None' with NaN
        d = d.fillna(value=np.nan, axis='columns')

        # determine the times
        dt = np.diff(d.index.unique())/60/1e9   # time difference in minutes

        dt = dt.astype('float64')
        m = stats.mode(dt)[0][0]  # most likely time steps for the data

        self._logger.debug('Determined data time step to be %f minutes' % m)

        # produce an index that is complete and tz aware.
        t = date_range(start_date, end_date, timedelta(minutes=m))

        # Make sure incoming mysql data is also tz aware
        d = d.tz_localize(time_zone)

        # now we need to parse the data frame
        df = {}
        variables = variables.split(',')
        for v in variables:
            self._logger.debug('Creating dataframe for {}'.format(v))

            # create an empty dataframe
            dp = pd.DataFrame(index=t, columns=station_ids)
            dp.index.name = 'date_time'

            for s in station_ids:
                dp[s] = d[v][d['station_id'] == s].copy()

            df[v] = dp

        return df

    #  TODO: is this used anymore?
    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()


def date_range(start_date, end_date, increment):
    """
    Calculate a list between start and end date with
    an increment
    """
    result = []
    nxt = start_date

    while nxt <= end_date:
        result.append(nxt)
        nxt += increment

    return np.array(result)
