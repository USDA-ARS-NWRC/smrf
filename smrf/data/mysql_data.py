'''
Created on Dec 22, 2015

Read in metadata and data from a MySQL database
The table columns will most likely be hardcoded for ease 
of development and users will require the specific table setup

@author: scott
'''

import numpy as np
import mysql.connector
from mysql.connector import errorcode

host = '10.200.28.203'
user = 'scott'
password = 'avalanche'

# host = 'localhost'
# user = 'wxuser_v2'
# password = 'x340hm4h980r'

db = 'weather_v2'


class database:
    '''
    Database class for querying metadata and station data
    '''
    
    _db_connection = None
    _db_cur = None
    station_ids = None
    client = None
    
    def __init__(self, user, password, host, db):
        
        try:
            cnx = mysql.connector.connect(user=user, password=password,
                                      host=host,
                                      database=db)
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        
        self._db_connection = cnx
        self._db_cur = self._db_connection.cursor()
        
        
    def metadata(self, station_ids=None, client=None):
        '''
        Similar to the CorrectWxData database call
        Get the metadata from the database for either the specified stations
        or for the specific group of stations in client
        '''
        
        return True
    
    
    def get_data(self):
        '''
        Get data from the database, either for the specified stations
        or for the specific group of stations in client
        '''
        
        return True
        

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()
    
        



