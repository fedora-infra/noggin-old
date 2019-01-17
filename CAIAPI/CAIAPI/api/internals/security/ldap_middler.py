from ipapython import ipaldap
from ipapython.ipautil import private_ccache
from ipalib.install.kinit import kinit_keytab
import threading

from CAIAPI import APP

ldapcache = threading.local()


class LdapClient(object):
    @property
    def _conn(self):
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

    def __init__(self, logger, user_token_info, client_info):
        self._user_token_info = user_token_info
        self._client_info = client_info
        logger.info("User token: %s" % user_token_info)
        logger.info("CLient info: %s" % client_info)

        logger.info("Connection: %s" % self._conn)

    @property
    def current_user(self):
        """ Get a UserShim object for the logged in user. """
        return self.get_user(self._user_token_info['sub'])

    def get_user(self, username):
        """ Get a UserShim object for a user. """
        return None


class Shim(object):
    def __init__(self, client, object_DN, object_type):
        # TODO: Add the base DN to the end of object_DN
        self._entry = None
        self._activated = False
        self._client = client
        self._object_DN = object_DN
        self._object_type = object_type

    @property
    def _attrs_read(self):
        """ Returns a list of attributes allowed to be read.

        This is filtered for both the client and the user. """
        # TODO: Implement
        return ['uid']

    @property
    def _attrs_write(self):
        """ Returns a list of attributes allowed to be written.

        This is filtered for both the client and the user. """
        # TODO: Implement
        return []

    def _ensure_entry(self):
        if self._entry is None:
            self._entry = self._client.get_entry(
                self.object_DN,
                attr_list=self._attrs_read
            )

    def __getattr__(self, attribute):
        if attribute not in self._attrs_read:
            # TODO: Raise new exception
            raise ValueError("NO ACCESS")
        self._ensure_entry()
        return self._entry[attribute]

    def __setattr__(self, attribute, value):
        if not self._activated:
            raise ValueError("Shim is not entered")
        if attribute not in self._attrs_write:
            # TODO: Raise new exception
            raise ValueError("NO WRITE ACCESS")
        self._ensure_entry()
        self._entry[attribute] = value

    def __enter__(self):
        self._activated = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._client.update_entry(self._entry)
        self._activated = False
        # Re-raise the provided exception
        return False


class UserShim(Shim):
    def __init__(self, client, username):
        user_dn = "%s,CN=foobar" % username
        super().__init__(client, user_dn, 'user')


class GroupShim(Shim):
    def __init__(self, client, groupname):
        group_dn = "%s,CN=foobar" % groupname
        super().__init__(client, group_dn, 'group')
