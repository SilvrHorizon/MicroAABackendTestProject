from flask import jsonify, request

from app import db
from app.models import User
from app.utilities import email_is_valid

from . import blueprint
from .functions import api_paginate_query, get_pagination_page, make_bad_request, make_error_response
from .auth import login_required

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

    user = None
    try:
        user = User.from_dict(data)
    except TypeError as e:
        return make_bad_request(str(e))
    
    
    db.session.add(user)
    db.session.commit()


    return user.to_dict(), 201

# TODO Create simple testsd
@blueprint.route('/users/<user_public_id>', methods=['PUT'])
@login_required
def update_user(current_user, user_public_id):
    user_to_update = User.query.filter_by(public_id=user_public_id).first_or_404()

    if not user_to_update.modifiable_by(current_user):
        return make_error_response(401, "You do not have the permission to update this user")

    if 'is_admin' in request.json:        
        # Check if user tries to update is_admin without current_user being an admin
        if request.json['is_admin'] != user_to_update.is_admin and not current_user.is_admin:
            return make_bad_request(401, "Only admins can promote or demote")
    
    try:
        user_to_update.update_fields(request.json)
    except TypeError as e:
        return make_bad_request(str(e))

    db.session.commit()
    return user_to_update.to_dict()

@blueprint.route('/users/<string:public_id>', methods=['DELETE'])
@login_required
def delete_user(current_user, public_id):
    to_delete = User.query.filter_by(public_id=public_id).first_or_404()

    if not to_delete.modifiable_by(current_user):
        return make_bad_request(401, "You can only delete your own account, unless you are an admin")

    db.session.delete(to_delete)
    db.session.commit()

    return {"status": "success"}, 200

@blueprint.route('/users/<string:user_public_id>/demote', methods=['POST'])
@login_required
def demote_user(current_user, user_public_id):
    if not current_user.is_admin:
        return make_error_response(401, "Only admins can demote users")
    
    user = User.query.filter_by(public_id=user_public_id).first_or_404()
    if not user:
        return make_error_response(404, "User not found")
    
    user.update_fields(
        dict(
            is_admin=False
        )
    )

    db.session.commit()
    return {"status": "success"}, 200



@blueprint.route('/users/<user_public_id>/promote', methods=["POST"])
@login_required
def promote_user(current_user, user_public_id):
    if not current_user.is_admin:
        return make_error_response(401, "Only admins can promote users")
    
    user = User.query.filter_by(public_id=user_public_id).first()
    if not user:
        return make_error_response(404, "User not found")
    
    user.is_admin = True
    db.session.commit()
    return {"status": "success"}, 200

