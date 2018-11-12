from CAIAPI.api.internals.exceptions import APIUnauthorizedError
from CAIAPI.api.internals.middlewares import Middleware
from CAIAPI.oidc import oidc


# Security sensitive middlewares
class UserAuthMiddleware(Middleware):
    def __init__(self, required_scopes):
        self.required_scopes = required_scopes

    def request_infos(self):
        raise APIUnauthorizedError("No authentication implemented yet")
