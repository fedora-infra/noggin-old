from CAIAPI.api import API

api = API(1)

@api
@api.register('', 'GET')
@api.return_code(200, "Hello")
@api.no_client_auth
@api.no_user_auth
def index():
    return {"message": "Greetings"}

@api
@api.register('', 'POST')
@api.return_code(200, "Hello")
@api.argument('name', 'User name to say hello to')
@api.paged
@api.no_client_auth
@api.user_auth(['testscope'])
def index(name, user, page, perpage):
    return {
        "message": "Greetings, %s. CAIAPI says hi!" % name,
        "page": page,
        "perpage": perpage,
        "numpages": 42,
        "user": user,
    }
