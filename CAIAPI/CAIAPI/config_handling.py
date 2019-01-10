from binascii import a2b_hex
from cryptography.hazmat.primitives import hashes

def check_config(app):
    errors = []
    if not app.config['OIDC_CLIENT_SECRETS']:
        errors.append("Configure OpenID Connect client secrets")

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
