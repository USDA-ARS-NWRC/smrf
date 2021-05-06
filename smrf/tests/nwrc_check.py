import requests


class NWRCCheck(object):

    HOST = '10.200.28.50/dashboard'
    URL = 'http://' + HOST

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
