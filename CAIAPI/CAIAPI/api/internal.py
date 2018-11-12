from flask import Blueprint, request, jsonify
import logging


from CAIAPI.api.middlewares import *
from CAIAPI.api.exceptions import APIError


def get_apifunc(arg):
    """ Helper function to provide an APIFunc instance.

    If the arg is already an APIFunc, returns arg, if it's a callable
    (supposedly view function), it returns a new APIFunc instance.
    This is primarily used so the API decorators can be used in any order.
    """
    if isinstance(arg, APIFunc):
        return arg

    if callable(arg):
        return APIFunc(arg)

    raise ValueError("Argument %s is neither apifunc nor callable" % arg)


def wrapperfunc(func):
    """ Defines an API decorator.

    Functions decorated with this work as an API decorator that take possible
    arguments, after which they get the argument values and an APIFunc instance
    they can add information to.
    """
    def wrap_wrapper(self, *args, **kwargs):
        def inner_wrapper(arg):
            apifunc = get_apifunc(arg)
            func(self, apifunc, *args, **kwargs)
            return apifunc
        return inner_wrapper
    return wrap_wrapper


def wrapperfunc_noargs(func):
    """ Defines an API decorator without arguments.

    For more info, see `wrapperfunc`.
    """
    def wrap_noargs_wrapper(self, arg):
        return wrapperfunc(func)(self)(arg)
    return wrap_noargs_wrapper


def generate_viewfunc(final_viewfunc, middlewares):
    """ Generates a function that operates as Flask viewfunc.

    This function will first call all the middlewares, add their information
    and return early if they return something special.

    After that, it calls the actual view function with the middleware arguments
    as keyword arguments.
    """
    def caller():
        intermediates = []
        kwargs = {}

        for middleware in middlewares:
            output = middleware.request_infos()
            if output:
                logging.debug("Middleware %s generated kwargs: %s",
                              middleware,
                              output)
                kwargs.update(output)

            result = middleware.intermediate_viewfunc()
            if result is not None:
                logging.debug("Middleware %s returned: %s",
                              middleware,
                              result)
                return result

        logging.debug("Calling final viewfunc %s with args %s",
                      final_viewfunc,
                      kwargs)
        return final_viewfunc(**kwargs)
    return caller


class APIFunc(object):
    """ Class to keep intermediate API function information.

    This class is used to carry through the current API decorator information
    until it is finally registered.
    """
    def __init__(self, viewfunc):
        self.viewfunc = viewfunc
        self.middlewares = []
        self.route = None
        self.arguments = []
        self.return_codes = []
        self.client_auth = None
        self.user_auth = None

    def get_viewfunc(self):
        """ Function to generate the actual Flask view function.

        This generates a view function that can be registered to a Flask
        url mapping.
        It injects the middleware functions to handle the decorators for this
        API call.
        """
        # Generate some common middlewares
        if self.arguments:
            self.middlewares.append(ArgumentMiddleware(self.arguments))

        # Return the viewfunc, wrapped with requested middlewares
        return generate_viewfunc(self.viewfunc, self.middlewares)

    def check(self):
        """ Performs various checks on the APIFunc.

        This verifies that at least one route is registered, that client and
        user authentication requirements have been indicated, and other checks.

        It raises a ValueError if any of the checks failed, but does not return
        anything if everything is fine.
        """
        invalid = []

        if not self.route:
            invalid.append(('route', 'missing'))
        elif not self.route[1] in ['GET', 'POST', 'PUT']:
            invalid.append(('route', 'invalid method: %s' % self.route[1]))

        if 200 not in [rcode[0] for rcode in self.return_codes]:
            invalid.append(('return_codes', 'missing return code for 200'))

        if self.client_auth is None:
            invalid.append(
                ('client_auth', 'Please provide client auth requirement'))

        if self.user_auth is None:
            invalid.append(
                ('user_auth', 'Please provide user auth requirement'))

        if invalid:
            msgs = []
            for error in invalid:
                msgs.append("%s: %s" % error)
            raise ValueError(
                "APIFunc for %s is invalid: %s"
                % (self.viewfunc.__name__,
                   ', '.join(msgs)))


def error_handler(func):
    """ Wrapper view function to handle errors.

    This returns a Flask view function that catches and handles Exceptions
    and APIErrors by returning a correct JSON result.
    """
    def handle_caller():
        try:
            response = func()
            if not isinstance(response, dict):
                raise ValueError(
                    "Call function %s (method %s) returned non-dict"
                    % (func.methods_to_viewfunc.get(request.method),
                       request.method)
                )
            if 'success' not in response:
                response['success'] = True
            return jsonify(response)
        except APIError as err:
            logging.warning("API error occured, code: %s, msg: %s",
                            err.code,
                            err.internal or err.message)
            response = {'success': False,
                        'error': err.message}
            return jsonify(response), err.code
        except Exception:
            logging.exception("Unexpected error during request processing")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
            }), 500
    return handle_caller


def route_multiplexer(methods_to_viewfunc):
    """ Wrapper view function to decide which view function to call.

    This determines and calls the intended view function based on the HTTP
    method.
    """
    def multiplexer():
        viewfunc = methods_to_viewfunc.get(request.method)
        if not viewfunc:
            raise Exception("No viewfunc found somehow?")
        return viewfunc()
    multiplexer.methods_to_viewfunc = methods_to_viewfunc
    return multiplexer


def register_to_blueprint(blueprint, route, methods_to_apifunc):
    """ Registers a set of view functions to a blueprint.

    This binds a `route_multiplexer` to `route` on the selected blueprint.
    """
    methods_to_viewfunc = {}
    for method in methods_to_apifunc:
        methods_to_viewfunc[method] = methods_to_apifunc[method].get_viewfunc()

    if 'HEAD' not in methods_to_viewfunc and 'GET' in methods_to_viewfunc:
        methods_to_viewfunc['HEAD'] = methods_to_viewfunc['GET']

    blueprint.add_url_rule(
        route,
        view_func=error_handler(route_multiplexer(methods_to_viewfunc)),
        methods=list(methods_to_viewfunc.keys()))
