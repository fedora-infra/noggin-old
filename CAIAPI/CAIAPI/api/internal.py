from flask import Blueprint, request


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
        elif not self.route[1] in ['GET', 'POST', 'PUT']:
            invalid.append(('route', 'invalid method: %s' % self.route[1]))

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


def route_multiplexer(methods_to_viewfunc):
    def multiplexer():
        viewfunc = methods_to_viewfunc.get(request.method)
        if not viewfunc:
            raise Exception("No viewfunc found somehow?")
        return viewfunc()
    return multiplexer


def register_to_blueprint(blueprint, route, methods_to_viewfunc):
    blueprint.add_url_rule(
        route,
        view_func=route_multiplexer(methods_to_viewfunc),
        methods=list(methods_to_viewfunc.keys()))
