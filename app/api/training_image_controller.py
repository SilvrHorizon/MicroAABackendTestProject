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
def get_training_images(current_user):
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


@blueprint.route("/training_images", methods=['POST'])
@login_required
def create_training_image(current_user):
    data = request.form.copy()
    
    # Check if dictionary is empty and if so load the data from passed json instead
    if not data:
        data = {}

    if 'user' not in data:
        data['user'] = current_user.public_id
    
    if not current_user.is_admin and data['user'] != current_user.public_id:
        return make_error_response(401, "Only admins can create images that belong to other users. You can only create an image that belongs to you") 

    if 'image' not in request.files:
        return make_bad_request("No image included")
    
    dbImage = None
    try:
        dbImage = TrainingImage.from_dict(data)
    except ValueError as e:
        return make_bad_request(str(e))

    image = request.files["image"]

    try:
        dbImage.set_image(image.stream)
    except ValueError as e:
        return make_bad_request(str(e))
    
    db.session.add(dbImage)
    db.session.commit()



    return jsonify(dbImage.to_dict()), 201
