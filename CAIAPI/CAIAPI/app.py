# Licensed under the terms of the GNU GPL License version 2

import flask

APP = flask.Flask(__name__)
APP.config.from_object('CAIAPI.default_config')

@APP.route('/')
def index():
    ''' Display the index page. '''
    return 'Hello CAIAPI'
