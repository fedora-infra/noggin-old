from ipapython import ipaldap
import threading
import logging


ldapcache = threading.local()


def get_connection():
    pass


class LdapClient(object):
    def __init__(self, logger, user_token_info, client_info):
        self._user_token_info = user_token_info
        self._client_info = client_info
        logger.info("User token: %s" % user_token_info)
        logger.info("CLient info: %s" % client_info)

# TODO: UserWrapper and GroupWrapper
