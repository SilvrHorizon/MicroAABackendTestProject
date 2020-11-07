from flask import request, jsonify

from app import db
from app.models import TrainingImage, User  # Try to remove user import


from . import blueprint
from .auth import login_required
from .functions import api_paginate_query, make_bad_request, make_error_response


@blueprint.route("/training_images/<string:public_id>", methods=['GET'])
def get_training_image(public_id):
    image = TrainingImage.query.filter_by(public_id=public_id).first()
    
    if image:
        return jsonify(image.to_dict())
    
    return make_error_response(404)

@blueprint.route("/training_images", methods=['GET'])
def get_training_images():
    endpoint = "api.get_training_images"
    query = TrainingImage.query
    user_public_id = request.args.get('user')

    if user_public_id:
        query = query.filter_by(user=User.query.filter_by(public_id=user_public_id).first())

    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    return jsonify(api_paginate_query(query, page=page, endpoint=endpoint, user=user_public_id))


@blueprint.route('/training_images/<string:public_id>', methods=['DELETE'])
@login_required
def delete_training_image(current_user, public_id):
    training_image = TrainingImage.query.filter_by(public_id=public_id).first_or_404()

    if not training_image.modifiable_by(current_user):
        return make_error_response(401, "You do not have the permission to delete this")
    
    training_image.delete_image()      # Deletes the acctual image
    db.session.delete(training_image)  # Deletes the database representation
    db.session.commit()
    return {"status": "success"}


@blueprint.route("/training_images", methods=['POST'])
@login_required
def create_training_image(current_user):
    data = request.form.copy() if request.form else {}
    if 'user' not in data:
        data['user'] = current_user.public_id
    
    if data['user'] != current_user.public_id and not current_user.is_admin:
        return make_error_response(401, "Only admins can create images that belong to other users. You can only create an image that belongs to you") 

    if 'image' not in request.files:
        return make_bad_request("No image included")
    
    dbImage = None
    try:
        dbImage = TrainingImage.from_dict(data)
    except ValueError as e:
        return make_bad_request(str(e))

    if not dbImage.modifiable_by(current_user):
        return make_error_response(401, "You do not have the permission to create a training image that is a child of the user you requested")

    image = request.files["image"]

    try:
        dbImage.set_image(image.stream)
    except ValueError as e:
        return make_bad_request(str(e))
    
    db.session.add(dbImage)
    db.session.commit()
    return jsonify(dbImage.to_dict()), 201
