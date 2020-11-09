from flask import abort, current_app, jsonify, request

from app import db
from app.models import User

from . import blueprint
from .errors import make_bad_request_response, make_error_response, make_unauthorized_response
from .pagination import api_paginate_query, get_pagination_page

from .auth import login_required

@blueprint.route('/users/<string:public_id>', methods=['GET'])
def get_user(public_id):
    user = User.query.filter_by(public_id=public_id).first_or_404()
    return jsonify(user.to_dict())
    
@blueprint.route('/users', methods=["GET"])
def get_users():
    page = get_pagination_page()
    query = User.query

    return api_paginate_query(query, endpoint="api.get_users", per_page=current_app.config["ITEMS_PER_PAGE"], page=page)


def abort_if_missing_fields(data):
    if 'email' not in data or 'password' not in data:
        abort(400, "Email and password must be included in create request")

@blueprint.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}

    abort_if_missing_fields(data)

    if User.query.filter_by(email=data['email']).count() > 0:
        return make_bad_request_response("Email already in use")

    user = None
    try:
        user = User.from_dict(data)
    except (ValueError, TypeError) as e:
        return make_bad_request_response(str(e))
    
    db.session.add(user)
    db.session.commit()

    return user.to_dict(), 201

def abort_if_non_admin_tries_promote_or_demote(user_trying):
    if 'is_admin' in request.json:        
        if request.json['is_admin'] != user_trying.is_admin and not user_trying.is_admin:
            abort(401, "Only admins can promote or demote")



@blueprint.route('/users/<user_public_id>', methods=['PUT'])
@login_required
def update_user(current_user, user_public_id):
    user_to_update = User.query.filter_by(public_id=user_public_id).first_or_404()

    if not user_to_update.modifiable_by(current_user):
        return make_unauthorized_response("You do not have the permission to update this user")

    abort_if_non_admin_tries_promote_or_demote(current_user)
    
    try:
        user_to_update.update_attributes(request.json)
    except (ValueError, TypeError) as e:
        return make_bad_request_response(str(e))

    db.session.commit()
    return user_to_update.to_dict()

@blueprint.route('/users/<string:public_id>', methods=['DELETE'])
@login_required
def delete_user(current_user, public_id):
    to_delete = User.query.filter_by(public_id=public_id).first_or_404()

    if not to_delete.modifiable_by(current_user):
        return make_error_response("You can only delete your own account, unless you are an admin")

    db.session.delete(to_delete)
    db.session.commit()

    return {"status": "success"}, 200

@blueprint.route('/users/<string:user_public_id>/demote', methods=['POST'])
@login_required
def demote_user(current_user, user_public_id):
    if not current_user.is_admin:
        return make_unauthorized_response("Only admins can demote users")
    
    user = User.query.filter_by(public_id=user_public_id).first_or_404()
    if not user:
        return make_error_response(404, "User not found")
    
    user.update_attributes(
        dict(
            is_admin=False
        )
    )

    db.session.commit()
    return {"status": "success"}, 200



@blueprint.route('/users/<string:user_public_id>/promote', methods=["POST"])
@login_required
def promote_user(current_user, user_public_id):
    if not current_user.is_admin:
        return make_unauthorized_response("Only admins can promote users")
    
    user = User.query.filter_by(public_id=user_public_id).first_or_404()
    
    user.update_attributes(
        dict(
            is_admin=True
        )
    )

    db.session.commit()
    return {"status": "success"}, 200

