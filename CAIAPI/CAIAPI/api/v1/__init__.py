from flask import Blueprint


api_v1 = Blueprint('api_v1', __name__)


@api_v1.route('/')
def index():
    print(dir(api_v1))
    return "API version 1"
