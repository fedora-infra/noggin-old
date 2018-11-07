# Licensed under the terms of the GNU GPL License version 2

import os

import flask

import noggin.mockapi

APP = flask.Flask(__name__)
APP.config.from_object('noggin.default_config')


blueprint = flask.Blueprint('theme', __name__, static_url_path='/theme/static', static_folder="themes/"+APP.config['THEME']+"/static/", template_folder="themes/"+APP.config['THEME']+"/templates/")
APP.register_blueprint(blueprint)


## The flask application itself

@APP.route('/')
def index():
    ''' Display the index page. '''

    return flask.render_template(
        'index.html',
    )

@APP.route('/users')
def users():
    ''' Display the user list page. '''

    searchterm = flask.request.args.get('searchterm', None)

    users = nogginmockapi.get_users(searchterm=searchterm)

    return flask.render_template(
        'users.html',
        users=users,
    )

@APP.route('/users/<username>')
def userdetail(username=None):
    ''' Display the user detail page. '''

    user = nogginmockapi.get_user(username=username)

    return flask.render_template(
        'user.html',
        user=user,
    )

@APP.route('/create')
def create_account():
    ''' 
        Page for creating a new account
    '''
    return flask.render_template(
        'create_account.html',
    )

@APP.route('/login')
def login():
    return 'No login yet'
