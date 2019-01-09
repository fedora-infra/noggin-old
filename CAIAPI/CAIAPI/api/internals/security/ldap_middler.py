from ipapython import ipaldap
import threading


ldapcache = threading.local()


def get_connection():
    pass


class LdapClient(object):
    def __init__(self, user_token_info, client_info):
        raise NotImplementedError("Ldap Client not yet implemented")

# TODO: UserWrapper and GroupWrapper
