# Licensed under the terms of the GNU GPL License version 2

import flask

from CAIAPI import APP
from CAIAPI.api.internals.selfdocumentation import (
    documentation_viewfunc,
    documentation_json_viewfunc,
)
from CAIAPI.config_handling import check_config
from CAIAPI.oidc import oidc

APP.config.from_object('CAIAPI.default_config')
APP.config.from_envvar('CAIAPI_SETTINGS')
oidc.init_app(APP)

check_config(APP)

from CAIAPI.api.v1 import api as api_v1

APIS = {
    'v1': api_v1,
}
DEFAULT_API = "v1"

for api_v in APIS:
    APP.register_blueprint(APIS[api_v].get_blueprint(), url_prefix='/' + api_v)
    APP.add_url_rule(
        "/doc/%s" % api_v,
        view_func=documentation_viewfunc(APIS[api_v]),
        methods=["GET"])
    APP.add_url_rule(
        "/doc/%s.json" % api_v,
        view_func=documentation_json_viewfunc(APIS[api_v]),
        methods=["GET"])


@APP.route('/')
def index():
    return flask.jsonify({
        'api_versions': list(APIS.keys()),
        'default_version': DEFAULT_API,
    })
