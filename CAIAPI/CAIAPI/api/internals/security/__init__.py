from base64 import b64decode
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from flask import request, g
import threading
import secrets

from CAIAPI.api.internals.exceptions import (
    APIUnauthorizedError,
    APIForbiddenError,
)
from CAIAPI import APP
from CAIAPI.api.internals.middlewares import Middleware
from CAIAPI.oidc import oidc


AUTH_HDRS        = {'WWW-Authenticate': 'Bearer'}
AUTH_CLIENT_HDRS = {'WWW-Authenticate': 'CAIAPI-Client'}

# We generate a random key per thread. This key is used for unknown clients to
# prevent a timing side-channel. We generate one randomly per thread so that
# an attacker can't just brute-force to find the server key, but we also don't
# generate it per request, since generating random bytes takes time.
class ThreadKeys(threading.local):
    def __getattr__(self, key):
        if key == 'unknown_client_key':
            self.unknown_client_key = secrets.token_bytes(32)
            return self.unknown_client_key
        raise AttributeError("No %s attribute" % key)

threadkeys = ThreadKeys()


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
    elif hash_name == 'sha512':
        return hashes.SHA512()
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
        hashname, digest = client_sig.rsplit(':', 1)
        hashmethod = get_hash_from_name(hashname)
        digest = b64decode(digest)

        if len(digest) != hashmethod.digest_size:
            raise APIUnauthorizedError("Invalid signature length for hash",
                                       headers=AUTH_CLIENT_HDRS)

        client_cfg = APP.config['CLIENTS'].get(client_name)
        # Try to avoid a timing sidechannel by using a random, thread-local
        # secret to compare the signature with. For information on this,
        # see the code on top of this file that generates it.
        # We set it here always so that even the first access
        #  (which generates the key) doesn't leak timing.
        client_key = threadkeys.unknown_client_key
        if client_cfg is not None:
            # Decoding from hex to binary is done by check_config
            client_key = client_cfg['secret']
            if len(client_key) < hashmethod.digest_size:
                # check_config makes sure that the client is at least able to
                # use any signing method, but the client might have tried to
                # use a hash method their secret is too short for.
                APP.logger.warning("Client secret for %s too short for hash "
                                   "algorithm %s, auth will fail",
                                   client_name,
                                   hashname)
                client_key = threadkeys.unknown_client_key
        token = get_request_oauth_token()

        h = hmac.HMAC(client_key,
                      hashmethod,
                      backend=default_backend())
        h.update(request.path.encode('utf-8'))
        h.update(b'_')
        h.update(request.method.lower().encode('utf-8'))
        h.update(b'_')
        if token:
            h.update(token.encode('utf-8'))
        else:
            h.update(b'NOUSER')
        h.update(b'_')
        h.update(request.get_data())
        try:
            h.verify(digest)
        except Exception as ex:
            raise APIUnauthorizedError("Client authentication failed for "
                                       "%s (existed: %s): %s"
                                       % (client_name,
                                          client_cfg is not None,
                                          ex),
                                       headers=AUTH_CLIENT_HDRS)

        if client_cfg is None:
            # This should not happen except for the INCREDIBLY rare case where
            #  *somehow* the client managed to produce a signature with the
            #  exact same random key as we happened to generate for this
            #  thread....
            # Theoretically, this is a 1 in 2^256 chance...
            raise APIUnauthorizedError("Client authentication against random "
                                       "key succeeded... Someone needs to go "
                                       "buy a lottery ticket...")

        # Strip "secret" so there's no chance of leaking it
        return {"client_info": {key: client_cfg[key]
                                for key in client_cfg
                                if key != 'secret'}}
