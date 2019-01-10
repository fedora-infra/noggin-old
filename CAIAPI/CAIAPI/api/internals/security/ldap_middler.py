from ipapython import ipaldap
from ipapython.ipautil import private_ccache
from ipalib.install.kinit import kinit_keytab
import threading

from CAIAPI import APP

from ipalib import krb_utils

ldapcache = threading.local()

import os
os.environ["KRB5_TRACE"]="/dev/stderr"

def get_connection():
    if not hasattr(ldapcache, 'connection'):
        conn = ipaldap.LDAPClient(
            ldap_uri=APP.config['LDAP_SERVER'],
            cacert=APP.config['LDAP_CACERT'],
        )
        with private_ccache() as ccache:
            kinit_keytab(
                principal='%s@%s' % (APP.config['KRB5_PRINCIPAL'],
                                     APP.config['KRB5_REALM']),
                keytab=APP.config['KRB5_KEYTAB'],
                ccache_name=ccache,
            )
            conn.gssapi_bind()

        ldapcache.connection = conn
    return ldapcache.connection


class LdapClient(object):
    def __init__(self, logger, user_token_info, client_info):
        self._user_token_info = user_token_info
        self._client_info = client_info
        logger.info("User token: %s" % user_token_info)
        logger.info("CLient info: %s" % client_info)

        logger.info("Connection: %s" % get_connection())


# TODO: UserWrapper and GroupWrapper
