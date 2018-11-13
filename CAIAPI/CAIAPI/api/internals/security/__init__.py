from flask import request, g

from CAIAPI.api.internals.exceptions import (
    APIUnauthorizedError,
    APIForbiddenError,
)
from CAIAPI.api.internals.middlewares import Middleware
from CAIAPI.oidc import oidc


AUTH_HDRS = {'WWW-Authenticate': 'Bearer'}


# Security sensitive middlewares
class UserAuthMiddleware(Middleware):
    def __init__(self, required_scopes):
        self.required_scopes = set(required_scopes)

    def request_infos(self):
        if 'Authorization' not in request.headers:
            raise APIUnauthorizedError("No token provided",
                                       headers=AUTH_HDRS)
        if not request.headers['Authorization'].lower().startswith('bearer '):
            raise APIUnauthorizedError("Non-bearer token",
                                       headers=AUTH_HDRS)
        token = request.headers['Authorization'].split(None, 1)[1].strip()
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
            raise APIForbiddenError("Token does not have required scopes",
                                    headers=AUTH_HDRS)
        return {"user": token_info}
