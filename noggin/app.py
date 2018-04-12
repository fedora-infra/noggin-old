# Licensed under the terms of the GNU GPL License version 2

import datetime
import logging
import logging.handlers
import os
import sys
import urlparse
from functools import wraps

import flask
from flask.ext.fas_openid import FAS

__version__ = '0.0.1'

APP = flask.Flask(__name__)
APP.config.from_object('noggin.default_config')

# Set up FAS extension
FAS = FAS(APP)


# Set up the logger
STDERR_LOG = logging.StreamHandler(sys.stderr)
STDERR_LOG.setLevel(logging.INFO)
APP.logger.addHandler(STDERR_LOG)

blueprint = flask.Blueprint('theme', __name__, static_url_path='/theme/static', static_folder="themes/"+APP.config['THEME']+"/static/", template_folder="themes/"+APP.config['THEME']+"/templates/")
APP.register_blueprint(blueprint)

## Flask specific utility function

def is_authenticated():
    """ Returns whether the user is currently authenticated or not. """
    return hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse.urlparse(flask.request.host_url)
    test_url = urlparse.urlparse(
        urlparse.urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def fas_login_required(function):
    ''' Flask decorator to ensure that the user is logged in against FAS.
    '''
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Do the actual work of the decorator. '''
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for(
                'login', next=flask.request.url))

        return function(*args, **kwargs)
    return decorated_function

## The flask application itself

@APP.route('/')
def index():
    ''' Display the index page. '''

    return flask.render_template(
        'index.html',
    )

@APP.route('/login', methods=['GET', 'POST'])
def login():
    ''' Login mechanism for this application.
    '''
    return_point = flask.url_for('index')
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            return_point = flask.request.args['next']

    # Avoid infinite loop
    if return_point == flask.url_for('login'):
        next_url = flask.url_for('index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(return_point)
    else:
        return FAS.login(return_url=return_point)

@APP.route('/logout')
def logout():
    ''' Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    '''
    next_url = flask.url_for('index')
    if 'next' in flask.request.values:
        if is_safe_url(flask.request.values['next']):
            next_url = flask.request.values['next']

    if next_url == flask.url_for('logout'):
        next_url = flask.url_for('index')
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash("You are no longer logged-in")
    return flask.redirect(next_url)


@APP.route('/create')
def create_account():
    ''' 
        Page for creating a new account
    '''
    return flask.render_template(
        'create_account.html',
    )


