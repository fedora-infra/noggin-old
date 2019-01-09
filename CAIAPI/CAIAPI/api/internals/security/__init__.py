from base64 import b64decode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from flask import request, g

from CAIAPI.api.internals.exceptions import (
    APIUnauthorizedError,
    APIForbiddenError,
)
from CAIAPI import APP
from CAIAPI.api.internals.middlewares import Middleware
from CAIAPI.oidc import oidc


AUTH_HDRS        = {'WWW-Authenticate': 'Bearer'}
AUTH_CLIENT_HDRS = {'WWW-Authenticate': 'CAIAPI-Client'}


def get_request_oauth_token():
    if 'Authorization' not in request.headers:
        return None
    if not request.headers['Authorization'].lower().startswith('bearer '):
        return None
    return request.headers['Authorization'].split(None, 1)[1].strip()


# Security sensitive middlewares
class UserAuthMiddleware(Middleware):
    def __init__(self, required_scopes):
        self.required_scopes = set(required_scopes)

    def request_infos(self):
        token = get_request_oauth_token()
        if token is None:
            raise APIUnauthorizedError("No bearer token provided",
                                       headers=AUTH_HDRS)
        # We take control of checking scopes ourselves so we can return a more
        # accurate HTTP status code
        validity = oidc.validate_token(token, scopes_required=None)
        if validity is not True:
            raise APIUnauthorizedError("Token not valid: %s" % validity,
                                       headers=AUTH_HDRS)
        token_info = g.oidc_token_info
        # Don't forget to do the checking of scopes
        token_scopes = set(token_info.get('scope', '').split(' '))
        if not self.required_scopes.issubset(token_scopes):
            raise APIForbiddenError("Token does not have required scopes")
        return {"user_tokeninfo": token_info}


def get_hash_from_name(hash_name):
    hash_name = hash_name.lower()
    if hash_name == 'sha256':
        return hashes.SHA256()
    # Add additionally supported hash methods here
    else:
        raise APIUnauthorizedError("Invalid signature header hash method")


class ClientAuthMiddleware(Middleware):
    def request_infos(self):
        if 'X-CAIAPI-Client-Name' not in request.headers:
            raise APIUnauthorizedError("No client auth provided",
                                       headers=AUTH_CLIENT_HDRS)
        if 'X-CAIAPI-Client-Sig' not in request.headers:
            raise APIUnauthorizedError("No client auth provided",
                                       headers=AUTH_CLIENT_HDRS)

        client_name = request.headers['X-CAIAPI-Client-Name']
        client_sig = request.headers['X-CAIAPI-Client-Sig']

        if ':' not in client_sig:
            raise APIUnauthorizedError("Invalid signature header format",
                                       headers=AUTH_CLIENT_HDRS)
        hashmethod, digest = client_sig.rsplit(':', 1)
        digest = b64decode(digest)

        client_cfg = APP.config['CLIENTS'].get(client_name)
        client_key = None
        if client_cfg is None:
            # Try to avoid a time difference by generating a random key
            # TODO: Generate random secret (SECURITY SENSITIVE: MUST BE RANDOM)
            client_key = ''
        else:
            client_key = client_cfg['secret']

        h = hmac.HMAC(client_key.encode('utf-8'),
                      get_hash_from_name(hashmethod),
                      backend=default_backend())
        h.update(request.path.encode('utf-8'))
        h.update(b'_')
        h.update(request.method.lower().encode('utf-8'))
        h.update(b'_')
        token = get_request_oauth_token()
        if token:
            h.update(token.encode('utf-8'))
        else:
            h.update(b'NOUSER')
        h.update(b'_')
        h.update(request.get_data())
        try:
            h.verify(digest)
        except Exception as ex:
            raise APIUnauthorizedError("Client authentication failed: %s" % ex,
                                       headers=AUTH_CLIENT_HDRS)

        # Strip "secret" so there's no chance of leaking it
        return {"client_info": {key: client_cfg[key]
                                for key in client_cfg
                                if key != 'secret'}}
