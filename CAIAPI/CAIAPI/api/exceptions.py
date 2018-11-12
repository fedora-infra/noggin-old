class APIError(RuntimeError):
    def __init__(self, code, message):
        self.code = code
        self.message = message


class APIInvalidRequest(APIError):
    def __init__(self, message):
        super(APIInvalidRequest, self).__init__(400, message)
