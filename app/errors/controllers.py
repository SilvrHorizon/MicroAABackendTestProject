from flask import jsonify, request
from . import blueprint
from werkzeug.exceptions import HTTPException

from ..api.errors import make_error_response as api_error_response, make_unauthorized_response as api_unauthorized_response


# Copied from: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxiii-application-programming-interfaces-apis
def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

@blueprint.route('/hello')
def hello():
    return "hello"



@blueprint.app_errorhandler(HTTPException)
def handle_exception(e):
    return api_error_response(e.code, e.description)

@blueprint.app_errorhandler(401)
def unauthorized_error(error):
    if wants_json_response():
        return api_unauthorized_response(error.description)