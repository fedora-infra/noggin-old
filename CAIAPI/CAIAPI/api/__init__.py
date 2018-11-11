from flask import Blueprint


def get_apifunc(arg):
    if isinstance(arg, APIFunc):
        return arg

    if callable(arg):
        return APIFunc(arg)

    raise ValueError("Argument %s is neither apifunc nor callable" % arg)


def wrapperfunc(func):
    def wrap_wrapper(self, *args, **kwargs):
        def inner_wrapper(arg):
            apifunc = get_apifunc(arg)
            func(self, apifunc, *args, **kwargs)
            return apifunc
        return inner_wrapper
    return wrap_wrapper


def wrapperfunc_noargs(func):
    def wrap_noargs_wrapper(self, arg):
        return wrapperfunc(func)(self)(arg)
    return wrap_noargs_wrapper


class API(object):
    def __init__(self, version):
        self.version = version
        self.blueprint = Blueprint(
            'api_v%s' % version,
            'CAIAPI.api.v%s' % version,
        )

    def __call__(self, apifunc):
        if not isinstance(apifunc, APIFunc):
            raise ValueError(
                "Argument %s is not APIFunc. Did you forget decorators?"
                % apifunc)

        apifunc.check()

        self.blueprint.add_url_rule(
            apifunc.route[0],
            view_func=apifunc.get_viewfunc(),
            methods=apifunc.route[1])

    @wrapperfunc
    def route(self, apifunc, funcname, http_methods):
        apifunc.route = (funcname, http_methods)

    @wrapperfunc
    def return_code(self, apifunc, return_code, description):
        apifunc.return_codes.append((return_code, description))

    @wrapperfunc
    def argument(self, apifunc, argname, description):
        apifunc.arguments.append((argname, description))

    @wrapperfunc_noargs
    def no_client_auth(self, apifunc):
        apifunc.client_auth = False

    @wrapperfunc_noargs
    def no_user_auth(self, apifunc):
        apifunc.user_auth = False


class APIFunc(object):
    def __init__(self, viewfunc):
        self.viewfunc = viewfunc
        self.route = None
        self.arguments = []
        self.return_codes = []
        self.client_auth = None
        self.user_auth = None

    def get_viewfunc(self):
        # Return the viewfunc, wrapped in any additional required functions
        return self.viewfunc

    def check(self):
        invalid = []

        if not self.route:
            invalid.append(('route', 'missing'))

        if 200 not in [rcode[0] for rcode in self.return_codes]:
            invalid.append(('return_codes', 'missing return code for 200'))

        if self.client_auth is None:
            invalid.append(('client_auth', 'Please provide client auth requirement'))

        if self.user_auth is None:
            invalid.append(('user_auth', 'Please provide user auth requirement'))

        if invalid:
            msgs = []
            for error in invalid:
                msgs.append("%s: %s" % error)
            raise ValueError(
                "APIFunc for %s is invalid: %s"
                % (self.viewfunc.__name__,
                   ', '.join(msgs)))
