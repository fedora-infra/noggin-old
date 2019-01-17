from ipapython import ipaldap
from ipapython.ipautil import private_ccache
from ipalib.install.kinit import kinit_keytab
import threading

from CAIAPI import APP

ldapcache = threading.local()


def base_dn():
    return ipaldap.DN(APP.config['LDAP_BASE'])


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
        self._logger = logger
        logger.info("User token: %s" % user_token_info)
        logger.info("CLient info: %s" % client_info)

        logger.info("Connection: %s" % self._conn)

    @property
    def current_user(self):
        """ Get a UserShim object for the logged in user. """
        return self.get_user(self._user_token_info['sub'])

    def get_user(self, username):
        """ Get a UserShim object for a user. """
        return UserShim(self._logger, self._conn, username)


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
        return ['uid']

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
        # TODO
        group_dn = "%s,CN=foobar" % groupname
        super().__init__(logger, client, group_dn, 'group')
