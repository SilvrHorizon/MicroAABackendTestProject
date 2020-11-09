from flask import abort, current_app, request, jsonify

from app import db
from app.models import TrainingImage, User


from . import blueprint
from .auth import login_required
from .errors import make_bad_request_response, make_error_response, make_unauthorized_response
from .pagination import api_paginate_query


@blueprint.route("/training_images/<string:public_id>", methods=['GET'])
def get_training_image(public_id):
    image = TrainingImage.query.filter_by(public_id=public_id).first_or_404()
    return jsonify(image.to_dict())


# Partially bad name, read function for better understanding 
def filter_by_user_or_404(query, user_public_id):

    # If there is no specific user to filter by, return the query as it is
    if user_public_id is None:
        return query
    
    user = User.query.filter_by(public_id=user_public_id).first()
    if not user:
        abort(404, f'No user with the public id of "{user_public_id}" exists')
    
    return query.filter_by(
        user=user
    )

@blueprint.route("/training_images", methods=['GET'])
def get_training_images():
    endpoint = "api.get_training_images"
    query = TrainingImage.query
    user_public_id = request.args.get('user')

    page = request.args.get('page')
    if not page:
        page = 1
    else:
        page = int(page)
    
    query = filter_by_user_or_404(query, user_public_id)
    return jsonify(api_paginate_query(query, page=page, per_page=current_app.config["ITEMS_PER_PAGE"], endpoint=endpoint, user=user_public_id))


@blueprint.route('/training_images/<string:public_id>', methods=['DELETE'])
@login_required
def delete_training_image(current_user, public_id):
    training_image = TrainingImage.query.filter_by(public_id=public_id).first_or_404()

    if not training_image.modifiable_by(current_user):
        return make_unauthorized_response("You do not have the permission to delete this")
    
    training_image.delete_image()      # Deletes the actual image
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
        return make_unauthorized_response("Only admins can create images that belong to other users. You can only create an image that belongs to you") 

    if 'image' not in request.files:
        return make_bad_request_response("No image included")
    
    dbImage = None
    try:
        dbImage = TrainingImage.from_dict(data)
    except ValueError as e:
        return make_bad_request_response(str(e))

    if not dbImage.modifiable_by(current_user):
        return make_unauthorized_response("You do not have the permission to create a training image that is a child of the user you requested")

    image = request.files["image"]

    try:
        dbImage.set_image(image.stream)
    except ValueError as e:
        return make_bad_request_response(str(e))
    
    db.session.add(dbImage)
    db.session.commit()
    return jsonify(dbImage.to_dict()), 201
