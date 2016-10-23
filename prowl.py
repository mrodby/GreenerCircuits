import os
import requests
import urllib.parse

class Prowl(object):

    def __init__(self, key=None):
        if key is not None:
            self.key = key
        # If prowl_key not set, complain and exit.
        elif 'prowl_key' not in os.environ:
            # TODO: throw exception instead of printing message and quitting
            print('prowl_key not set in environment')
            quit()
        self.key = os.environ['prowl_key']

    def notify(self, event, desc, info_url=None):
        """Send a notification via prowlapp.com.
           - Call with event = title, desc = what happened, info_url = URL
        """

        # Construct URL from base plus required parameters.
        url = ('http://api.prowlapp.com/publicapi/add?'
               + 'apikey=' + self.key
               + '&application=' + urllib.parse.quote('Greener Circuits')
               + '&event=' + urllib.parse.quote(event)
               + '&description=' + urllib.parse.quote(desc))
        if info_url is not None:
            url += '&url=' + urllib.parse.quote(info_url)
        try:
            requests.get(url)
        except(requests.exceptions.ConnectTimeout,
               requests.exceptions.ReadTimeout,
               requests.exceptions.ConnectionError):
            print('Error getting Prowl URL', url)
            # TODO: show actual exception with any relevant error message
