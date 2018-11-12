class APIError(RuntimeError):
    def __init__(self, code, message, internal=None):
        self.code = code
        self.message = message
        self.internal = internal


class APIInvalidRequest(APIError):
    def __init__(self, message, internal=None):
        super(APIInvalidRequest, self).__init__(400, message, internal)
