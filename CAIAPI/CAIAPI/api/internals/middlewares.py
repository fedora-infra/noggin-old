from flask import request


from CAIAPI.api.internals.exceptions import APIInvalidRequest, APICodingError


class Middleware(object):
    def request_infos(self):
        return {}

    def intermediate_viewfunc(self):
        return None

    def manipulate_response(self, resp, kwargs):
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


class PagingMiddleware(Middleware):
    PERPAGE_DEFAULT = 250
    PERPAGE_MAX = 250

    def request_infos(self):
        page = request.args.get("page", 1)
        perpage = request.args.get("perpage", PagingMiddleware.PERPAGE_DEFAULT)
        try:
            page = int(page)
        except ValueError:
            raise APIInvalidRequest("'page' must be an integer")
        try:
            perpage = int(perpage)
        except ValueError:
            raise APIInvalidRequest("'perpage' must be an integer")
        if page < 1:
            raise APIInvalidRequest("'page' must be >= 1")
        if perpage < 1:
            raise APIInvalidRequest("'perpage' must be >= 1")
        if perpage > PagingMiddleware.PERPAGE_MAX:
            perpage = PagingMiddleware.PERPAGE_MAX

        return {"page": page, "perpage": perpage}

    def manipulate_response(self, resp, kwargs):
        if "numpages" not in resp:
            raise APICodingError(
                "'numpages' missing in response from paged request")
        numpages = resp.pop("numpages")
        headers = {
            "X-CAIAPI-NumPages": numpages,
        }
        return resp, headers
