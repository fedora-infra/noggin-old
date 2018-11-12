from CAIAPI.api import API

api = API(1)

@api
@api.register('', 'GET')
@api.return_code(200, "Hello")
@api.no_client_auth
@api.no_user_auth
def index():
    return "API version 1"

@api
@api.register('', 'POST')
@api.return_code(200, "Hello")
@api.no_client_auth
@api.no_user_auth
def index():
    return "API version 1 via POST"
