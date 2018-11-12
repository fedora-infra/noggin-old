class APIError(RuntimeError):
    def __init__(self, code, message, internal=None, headers=None):
        self.code = code
        self.message = message
        self.internal = internal
        self.headers = headers or {}


class APIInvalidRequest(APIError):
    def __init__(self, message, internal=None):
        super(APIInvalidRequest, self).__init__(400, message, internal)


class APICodingError(APIError):
    def __init__(self, description):
        super(APICodingError, self).__init__(
            500,
            "API Coding error occured",
            description)


class APIUnauthorizedError(APIError):
    def __init__(self, internal, headers=None):
        super(APIUnauthorizedError, self).__init__(
            401,
            "Unauthorized",
            internal,
            headers)
