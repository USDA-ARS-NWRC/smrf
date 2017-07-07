"""
Created on Dec 22, 2015

Read in metadata and data from a MySQL database
The table columns will most likely be hardcoded for ease
of development and users will require the specific table setup

@author: scott
Version = 0.2.4
"""

import numpy as np
import scipy.stats as stats
import pandas as pd
import utm
import mysql.connector
# from mysql.connector import errorcode
from datetime import datetime, timedelta

import logging


class database:
    """
    Database class for querying metadata and station data
    """

    def __init__(self, user, password, host, db):

        try:
            cnx = mysql.connector.connect(user=user, password=password,
                                          host=host,
                                          database=db)

        except mysql.connector.Error as err:
            if err.errno == 1045:  # errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error('''Something is wrong with your
                                user name or password''')
            elif err.errno == 1049:  # errorcode.ER_BAD_DB_ERROR:
                logging.error("Database does not exist")
            else:
                logging.error(err)

        self._db_connection = cnx
        self._db_cur = self._db_connection.cursor()

        self._logger = logging.getLogger(__name__)
        self._logger.debug('Connected to MySQL database')

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

        # form the query
        if station_ids is not None:
            qry = "SELECT * FROM {0} WHERE primary_id IN ('{1}')".format(
                table, "','".join(station_ids))

        else:
            qry = """SELECT {0}.* FROM tbl_metadata INNER JOIN {1}
                 ON {2}.primary_id={3}.station_id WHERE {4}.client='{5}'""".format(
                    table, station_table, table, station_table,
                    station_table, client)

        self._logger.debug(qry)

        # execute the query
        d = pd.read_sql(qry, self._db_connection, index_col='primary_id')

        if d.empty:
            raise Exception('No metadata found for query')

        # check to see if UTM locations are calculated
        d[['X', 'Y']] = d.apply(to_utm, axis=1)

        return d

    def get_data(self, table, station_ids, start_date, end_date, variables):
        """
        Get data from the database, either for the specified stations
        or for the specific group of stations in client

        Args:
            table: table to load data from
            station_ids: list of station ids to get
            start_date: start of time period
            end_date: end of time period
            variable: string for variable to get
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

        t = date_range(start_date, end_date, timedelta(minutes=m))

        # now we need to parse the data frame
        df = {}
        variables = variables.split(',')
        for v in variables:

            # create an empty dataframe
            dp = pd.DataFrame(index=t, columns=station_ids)
            dp.index.name = 'date_time'
            for s in station_ids:
                dp[s] = d[v][d['station_id'] == s].copy()

            df[v] = dp

        return df

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()


def to_utm(row):
    """
    Convert a row from data frame to X,Y
    """
    if (row['X'] is None) and (row['Y'] is None):
        return pd.Series(utm.from_latlon(row['latitude'],
                                         row['longitude'])[:2])
    elif np.isnan(row['X']) and np.isnan(row['Y']):
        return pd.Series(utm.from_latlon(row['latitude'],
                                         row['longitude'])[:2])
    else:
        return pd.Series([row['X'], row['Y']])


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
