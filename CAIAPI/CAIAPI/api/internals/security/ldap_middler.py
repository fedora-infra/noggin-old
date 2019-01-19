from ipapython import ipaldap
from ipapython.ipautil import private_ccache
from ipalib.install.kinit import kinit_keytab
import threading

from CAIAPI import APP

ldapcache = threading.local()


def base_dn():
    return ipaldap.DN(APP.config['LDAP_BASE'])


def get_thread_ldap_connection():
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


# Attempt to pre-initialize at least the primary threads' LDAP conn
try:
    # The imports should be ordered such that this can be loaded after the
    # configuration has been loaded. But if that didn't work for some reason,
    # that is okay, and we just initialize LDAP on first request to the thread.
    if APP.config['LDAP_BASE'] is None:
        raise ValueError("Looks like import order was incorrect")
    get_thread_ldap_connection()
    APP.logger.debug("LDAP connection pre-heated for main thread")
except Exception as ex:
    APP.logger.info("Pre-heating LDAP connection failed: %s", ex)


class LazyLDAPConnection(object):
    def __init__(self):
        self._conn = None

    def __getattr__(self, attribute):
        if self._conn is None:
            APP.logger.debug("LDAP connection initialized to get %s",
                             attribute)
            self._conn = get_thread_ldap_connection()
        return getattr(self._conn, attribute)


class LdapClient(object):
    @property
    def _conn(self):
        return LazyLDAPConnection()

    def __init__(self, logger, user_token_info, client_info):
        self._user_token_info = user_token_info
        self._client_info = client_info
        self._logger = logger
        self._user_cache = {}

    @property
    def current_user(self):
        """ Get a UserShim object for the logged in user. """
        return self.get_user(self._user_token_info['sub'])

    def get_user(self, username):
        """ Get a UserShim object for a user. """
        if username not in self._user_cache:
            self._user_cache[username] = UserShim(
                self._logger,
                self._conn,
                username
            )
        return self._user_cache[username]


class Shim(object):
    def __init__(self, logger, client, object_DN, object_type):
        # TODO: Add the base DN to the end of object_DN
        self._logger = logger
        self._client = client
        self._object_DN = ipaldap.DN(*object_DN, base_dn())
        self._object_type = object_type

        self._entry = None
        self._activated = False

        logger.debug(
            "Shim initialized for type %s, DN: %s",
            self._object_type,
            self._object_DN)

    @property
    def _attrs_read(self):
        """ Returns a list of attributes allowed to be read.

        This is filtered for both the client and the user. """
        # TODO: Implement
        return ['uid', 'cn']

    @property
    def _attrs_write(self):
        """ Returns a list of attributes allowed to be written.

        This is filtered for both the client and the user. """
        # TODO: Implement
        return []

    def _assert_access(self, is_write, attribute):
        acl = None
        if is_write:
            acl = self._attrs_write
        else:
            acl = self._attrs_read
        if attribute not in acl:
            self._logger.error(
                "Forbidden access to attribute %s (write: %s)",
                attribute,
                is_write,
            )
            # TODO: Raise new exception
            raise ValueError("NO ACCESS TO ATTRIBUTE")

    def _ensure_entry(self):
        if self._entry is None:
            self._entry = self._client.get_entry(
                self._object_DN,
                attrs_list=self._attrs_read
            )

    def __getattr__(self, attribute):
        if attribute.startswith('_'):
            raise ValueError("Attempt to getattr internal attribute %s"
                             % attribute)
        self._logger.debug("Attempt to look up attribute %s", attribute)
        self._assert_access(False, attribute)
        self._ensure_entry()
        return self._entry[attribute]

    def __setattr__(self, attribute, value):
        if attribute.startswith('_'):
            return super().__setattr__(attribute, value)
        self._logger.debug("Attempt to write attribute %s", attribute)
        if not self._activated:
            raise ValueError("Shim is not entered")
        self._assert_access(True, attribute)
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
    def __init__(self, logger, client, username):
        user_dn = [('uid', username), ('cn', 'users'), ('cn', 'accounts')]
        super().__init__(logger, client, user_dn, 'user')


class GroupShim(Shim):
    def __init__(self, logger, client, groupname):
        group_dn = [('cn', groupname), ('cn', 'groups'), ('cn', 'accounts')]
        super().__init__(logger, client, group_dn, 'group')
