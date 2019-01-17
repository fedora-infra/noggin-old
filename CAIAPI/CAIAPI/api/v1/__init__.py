from CAIAPI.api import API

api = API(1)

@api
@api.register('', 'GET')
@api.return_code(200, "Hello")
@api.no_client_auth
@api.no_user_auth
def index(ldap):
    return {"message": "Greetings"}

@api
@api.register('ping', 'POST')
@api.return_code(200, "Hello")
@api.argument('name', 'User name to say hello to')
@api.paged
@api.client_auth
@api.user_auth('/testscope')
def ping(log, ldap, name, page, perpage):
    if page == 1:
        return {
            "message": "Greetings, %s. CAIAPI says hi!" % name,
            "page": page,
            "perpage": perpage,
        }, {"numpages": 2}
    else:
        return {
            "message": "Greetings, %s. CAIAPI greets you!" % name,
            "page": page,
            "perpage": perpage,
        }, {"numpages": 2}

@api
@api.register('whoami', 'GET')
@api.return_code(200, 'Hello')
@api.client_auth
@api.user_auth('/testscope')
def whoami(log, ldap):
    log.info("Whoami called")
    return ldap.current_user.uid[0]
