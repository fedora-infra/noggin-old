from flask import request


from CAIAPI.api.exceptions import APIInvalidRequest


class Middleware(object):
    def request_infos(self):
        return {}

    def intermediate_viewfunc(self):
        return None


class ArgumentMiddleware(Middleware):
    def __init__(self, arguments):
        self.arguments = arguments

    def request_infos(self):
        args = {}
        reqjson = request.json or {}
        hadreq = request.json is not None

        for argument in self.arguments:
            argkey = argument["name"]
            if argkey in reqjson:
                args[argkey] = reqjson[argkey]
            elif argument["required"]:
                if not hadreq:
                    raise APIInvalidRequest("JSON request required")
                raise APIInvalidRequest("Argument '%s' is required" % argkey)

        return args
