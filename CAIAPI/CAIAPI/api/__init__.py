from flask import Blueprint


from CAIAPI.api.internal import (
    APIFunc,
    wrapperfunc,
    wrapperfunc_noargs,
    register_to_blueprint,
)


class API(object):
    def __init__(self, version):
        self.version = version
        self.registered = {}

    def get_blueprint(self):
        blueprint = Blueprint(
            'api_v%s' % self.version,
            'CAIAPI.api.v%s' % self.version,
        )

        for route in self.registered:
            regs = self.registered[route]
            register_to_blueprint(
                blueprint,
                route,
                regs)

        return blueprint

    def __call__(self, apifunc):
        if not isinstance(apifunc, APIFunc):
            raise ValueError(
                "Argument %s is not APIFunc. Did you forget decorators?"
                % apifunc)

        apifunc.check()

        route_name, http_method = apifunc.route
        # Just make sure we always use the same case
        http_method = http_method.upper()
        if route_name in self.registered:
            if http_method in self.registered[route_name]:
                raise ValueError(
                    "HTTP method %s for route name %s registered twice"
                    % (http_method, route_name))
            self.registered[route_name][http_method] = apifunc
        else:
            self.registered[route_name] = {http_method: apifunc}

    @wrapperfunc
    def register(self, apifunc, funcname, http_method):
        apifunc.route = (funcname, http_method)

    @wrapperfunc
    def return_code(self, apifunc, return_code, description):
        apifunc.return_codes.append((return_code, description))

    @wrapperfunc
    def argument(self, apifunc, argname, description, required=False):
        apifunc.arguments.append({
            "name": argname,
            "description": description,
            "required": required,
        })

    @wrapperfunc_noargs
    def no_client_auth(self, apifunc):
        apifunc.client_auth = False

    @wrapperfunc_noargs
    def no_user_auth(self, apifunc):
        apifunc.user_auth = False
