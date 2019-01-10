from binascii import a2b_hex
from cryptography.hazmat.primitives import hashes


def check_config(app):
    errors = []
    if not app.config['OIDC_CLIENT_SECRETS']:
        errors.append("Configure OpenID Connect client secrets")

    if not app.config['LDAP_SERVER']:
        errors.append("Configure LDAP server")
    #elif not app.config['LDAP_SERVER'].startswith('ldaps://'):
    #    errors.append("Use ldaps:// to access ldap")
    if not app.config['KRB5_REALM']:
        errors.append("Configure kerberos realm")
    if not app.config['KRB5_PRINCIPAL']:
        errors.append("Configure kerberos user principal")
    if not app.config['KRB5_KEYTAB']:
        errors.append("Configure kerberos user keytab")

    # We make sure that all client secrets are long enough for at least the
    # shortest hash algorithm we support per RFC2104:
    # "In any case the minimal recommended length for K is L bytes
    #  (as the hash output length)"
    # This leaves the chance they use a hash with a longer digest_size, for
    # which their client secret won't be valid, but the ClientAuthMiddleware
    # handles that case: they get rejected.
    minlength = hashes.SHA256().digest_size
    for clientname in app.config['CLIENTS']:
        client = app.config['CLIENTS'][clientname]
        client['secret'] = a2b_hex(client['secret'])
        if len(client['secret']) < minlength:
            errors.append("Client secret for client %s is too short. Min: %d"
                          % (clientname, minlength))

    if errors:
        raise ValueError("Configuration errors: %s" % ", ".join(errors))
