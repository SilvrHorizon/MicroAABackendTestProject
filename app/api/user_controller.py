from flask import jsonify, request

from app import db
from app.models import User
from app.utilities import email_is_valid

from . import blueprint
from .functions import api_paginate_query, get_pagination_page, make_bad_request, make_error_response





@blueprint.route('/users/<string:public_id>', methods=['GET'])
def get_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    if user is not None:
        return jsonify(user.to_dict())
    return make_error_response(404)

@blueprint.route('/users', methods=["GET"])
def get_users():
    page = get_pagination_page()
    query = User.query
    return api_paginate_query(query, "api.get_users", page=page)



@blueprint.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}

    if 'email' not in data or 'password' not in data:
        return make_bad_request("Email and password must be included in create request")

    if not email_is_valid(data["email"]):
        return make_bad_request("Invalid email")

    if User.query.filter_by(email=data['email']).count() > 0:
        return make_bad_request("Email already in use")

    user = User.from_dict(data)
    db.session.add(user)
    db.session.commit()

    return user.to_dict(), 201