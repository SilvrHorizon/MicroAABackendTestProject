from flask import request, jsonify

from app import db
from app.models import TrainingImage, User  # Try to remove user import


from . import blueprint
from .functions import api_paginate_query, make_bad_request, make_error_response


@blueprint.route("/training_images/<string:public_id>", methods=['GET'])
def get_training_image(public_id):
    image = TrainingImage.query.file_type(public_id=public_id)
    if image:
        return image.to_dict()
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


@blueprint.route("/training_images", methods=['POST'])
def create_training_image():
    data = request.form

    # Check if dictionary is empty and if so load the data from passed json instead
    if not bool(data):
        data = request.json

    if 'user' not in data:
        make_bad_request("You must include the owner to the image")
    try:
        dbImage = TrainingImage.from_dict(data)

        image = request.files["image"]

        if image:
            dbImage.set_image(image.stream)

        db.session.add(dbImage)
        db.session.commit()

    except ValueError as e:
        return make_bad_request(str(e))
    return "test"
