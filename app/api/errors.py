from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def make_error_response(status_code, message=None):
    data = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    }

    if message:
        data["message"] = message

    response = jsonify(data)
    response.status_code = status_code
    return response

def make_unauthorized_response(message=None):
    return make_error_response(status_code=401, message=message)

def make_bad_request_response(message=None):
    return make_error_response(status_code=400, message=message)
