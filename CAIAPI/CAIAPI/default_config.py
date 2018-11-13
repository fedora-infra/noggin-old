# -*- coding: utf-8 -*-
import os

# Secret key used to generate the CRSF token, thus very private!
SECRET_KEY = 'CHANGEME'

# Some OpenID Connect defaults
OIDC_RESOURCE_SERVER_ONLY = True
OIDC_INTROSPECTION_AUTH_METHOD = 'client_secret_basic'
OIDC_CLIENT_SECRETS = os.getenv("OIDC_CLIENT_SECRETS")
