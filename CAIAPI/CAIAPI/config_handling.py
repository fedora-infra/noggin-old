def check_config(app):
    errors = []
    if not app.debug and app.config["SECRET_KEY"] == "CHANGEME":
        errors.append("Configure secret key")

    if errors:
        raise ValueError("Configuration errors: %s" % ", ".join(errors))
