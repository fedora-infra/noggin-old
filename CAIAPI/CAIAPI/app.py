# Licensed under the terms of the GNU GPL License version 2

import flask

from CAIAPI.api.selfdocumentation import documentation_viewfunc
from CAIAPI.api.v1 import api as api_v1

APIS = {
    'v1': api_v1,
}

APP = flask.Flask(__name__)
APP.config.from_object('CAIAPI.default_config')

for api_v in APIS:
    APP.register_blueprint(APIS[api_v].get_blueprint(), url_prefix='/' + api_v)
    APP.add_url_rule(
        "/documentation/%s" % api_v,
        view_func=documentation_viewfunc(APIS[api_v]),
        methods=["GET"])


@APP.route('/')
def index():
    return flask.jsonify({
        'api_versions': list(APIS.keys()),
    })
