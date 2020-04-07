import requests


class NWRCCheck(object):
    MYSQL_OPTIONS = {
        'user': 'unittest_user',
        'password': 'WsyR4Gp9JlFee6HwOHAQ',
        'host': '10.200.28.137',
        'database': 'weather_db',
        'metadata': 'tbl_metadata',
        'data_table': 'tbl_level2',
        'station_table': 'tbl_stations',
        'air_temp': 'air_temp',
        'vapor_pressure': 'vapor_pressure',
        'precip': 'precip_accum',
        'solar': 'solar_radiation',
        'wind_speed': 'wind_speed',
        'wind_direction': 'wind_direction',
        'cloud_factor': 'cloud_factor',
        'port': '32768'
    }
    URL = 'http://' + MYSQL_OPTIONS['host']

    @classmethod
    def in_network(cls):
        """
        Checks that were on the NWRC network
        """
        try:
            response = requests.get(cls.URL, timeout=1)
            return response.ok

        except requests.exceptions.RequestException:
            return False
