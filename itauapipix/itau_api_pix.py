from datetime import datetime, timedelta
import os
import requests
from requests.auth import AuthBase

import env_itauapipix as env

class BadCredentials(Exception):
    ...


class EmptyPixList(Exception):
    ...


if hasattr(env, 'PATH_SERVER_CERTS'):
    PATH_SERVER_CERTS = env.PATH_SERVER_CERTS
else:
    LIBPATH = os.path.dirname(os.path.abspath(__file__))
    PATH_SERVER_CERTS = LIBPATH+'/server_certs/'

PATH_CLIENT_CERTS = env.PATH_CLIENT_CERTS
SERVERS_CONF = {
    'PROD': {
        'auth': {
            'endpoint': 'https://sts.itau.com.br/api/oauth/token',
        },
        'api': {
            'endpoint': 'https://secure.api.itau/pix_recebimentos/v2/',
        },
    },

}


class ItauAUTH(AuthBase):

    def __init__(self, client_id, client_secret, client_certificate, endpoint, server_cert=None):
        self.credentials = (client_id, client_secret)
        self.certificate = env.PATH_CLIENT_CERTS + client_certificate
        self._token = None
        self.expires_in = None

        print("CLIENT_CERT", self.certificate)
        self.endpoint = endpoint

    @property
    def is_valid(self):
        now = datetime.now()
        if not self._token or not self.expires_in or self.expires_in <= now:
            return False
        return True

    @property
    def token(self):
        if not self.is_valid:
            self.renew()
        return self._token

    @token.setter
    def token(self, token):
        type_, value = token
        self._token = f'{type_} {value}'

    def handle_401(self, r, **kwargs):
        if r.status_code != 401:
            return r

        # force token renew
        self.renew()

        # Consume content and release the original connection
        # to allow our new request to reuse the same one.
        r.content
        r.close()
        prep = r.request.copy()

        prep.headers['Authorization'] = self.token
        prep.headers['x-itau-apikey'] = self.credentials[0]
        _r = r.connection.send(prep, **kwargs)
        _r.history.append(r)
        _r.request = prep

        return _r

    def renew(self):
        data = f"grant_type=client_credentials&client_id={self.credentials[0]}&client_secret={self.credentials[1]}"

        header= {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        resp = requests.post(self.endpoint, headers=header, cert=self.certificate, data=data)
        
        if resp.status_code == 401:
            raise BadCredentials()

        if resp.status_code == 400:
            raise RuntimeError(resp.json())

        json = resp.json()
        self.token = "Bearer", json['access_token']

        self.expires_in = datetime.now() + timedelta(seconds=json['expires_in'])

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        r.headers['x-itau-apikey'] = self.credentials[0]
        
        r.register_hook("response", self.handle_401)
        return r


class ItauSession(requests.Session):

    def __init__(self, auth, endpoint, server_cert=None):
        super().__init__()
        self.auth = auth
        self.endpoint = endpoint
        #self.server_cert = PATH_SERVER_CERTS + server_cert

    def request(self, method: str, path='', *args, **kwargs):
        url = self.endpoint + path
        # print(url)
        resp = super().request(method, url, *args, cert=self.auth.certificate, **kwargs)
        return resp


class ItauClient:
    AUTH = ItauAUTH
    SESSION = ItauSession

    def __init__(self, session):
        self.session = session

    @classmethod
    def from_credentials(cls, client_id: str,
                         client_secret: str, client_certificate: str, enviroment: str):
        server_auth = SERVERS_CONF[enviroment]['auth']
        auth = cls.AUTH(client_id, client_secret, client_certificate, **server_auth)
        server_api = SERVERS_CONF[enviroment]['api']
        session = cls.SESSION(auth, **server_api)
        return cls(session)

    def request(self, method, path='', params=None, data=None, *args, **kwargs):
        resp = self.session.request(method, path=path, params=params, data=data, *args, **kwargs)
        if resp.status_code == 404:
            raise EmptyPixList

        resp.raise_for_status()
        return resp

    # init_datetime: '2023-09-01T00:00:01UTC-3'
    def received_pixs(self, init_datetime, end_datetime):
        params = {
            'inicio': init_datetime,
            'fim': end_datetime
        }

        resp = self.request('get', path='pix', params=params)

        return resp
