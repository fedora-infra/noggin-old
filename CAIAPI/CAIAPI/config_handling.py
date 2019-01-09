def check_config(app):
    errors = []
    if not app.config['OIDC_CLIENT_SECRETS']:
        errors.append("Configure OpenID Connect client secrets")

    if errors:
        raise ValueError("Configuration errors: %s" % ", ".join(errors))
