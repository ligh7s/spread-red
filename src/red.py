# -*- coding: utf-8 -*-

# SpreadRED - Create a database of torrent metadata from a Gazelle site
# Copyright (C) 2018  lights <lights@tutanota.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Module to interact with the Redacted API"""

import time
import requests

class RequestException(Exception):
    """Error on HTTP request."""
    pass

class LoginException(Exception):
    """Error with logging in."""
    pass

class API:
    """Wrapper for the RED API. Make requests and scrape and stuff."""

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'puffintosh red tracking stuff 0.1',
    }

    def __init__(self, username, password, cookie):
        self.base_url = 'https://redacted.ch/'
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.last = time.time()
        self.username = username
        self.password = password
        self.cookie = cookie
        self.authkey = None
        self.login()

    def login(self):
        """Login to Redacted."""
        if self.username and self.password:
            data = {
                'username': self.username,
                'password': self.password
            }
            loginpage = self.base_url + '/login.php'
            try:
                response = self.session.post(loginpage, data=data)
                if response.status_code == 200:
                    acctinfo = self.request('index')
                    if 'authkey' in acctinfo:
                        self.authkey = acctinfo['authkey']
                    else:
                        raise LoginException
                else:
                    raise LoginException
            except Exception:
                raise LoginException
        else:  # Use session cookie
            self.session.cookies.clear()
            self.session.cookies['session'] = self.cookie

    def logout(self):
        """Log out from Redacted, only if used regular login credential method."""
        if self.username and self.password:
            self.session.get(self.base_url + '/logout.php?auth={}'.format(self.authkey))

    def request(self, action, **kwargs):
        """Make a request to the Gazelle API."""
        if time.time() - self.last < 2:
            time.sleep(2 - (time.time() - self.last))

        url = self.base_url + 'ajax.php'
        params = {'action': action}
        params.update(kwargs)
        resp = self.session.get(url, params=params, allow_redirects=False).json()
        self.last = time.time()
        if resp['status'] != 'success':
            raise RequestException
        return resp['response']

    def get_torrent(self, torrentid):
        """Get the response JSON for a torrent."""
        data = {'id': torrentid}
        return self.request('torrent', **data)

