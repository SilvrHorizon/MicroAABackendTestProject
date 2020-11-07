from flask import jsonify, request, send_file

import io
import PIL

from app import db
from app.models import ClassifiedArea, TrainingImage


from . import blueprint
from .functions import api_paginate_query, get_pagination_page, make_bad_request, make_error_response

from .auth import login_required


def filter_by_training_image(query, training_image_public_id):
    if training_image_public_id is None:
        return query
    
    training_image = TrainingImage.query.filter_by(public_id=training_image_public_id).first()
    if not training_image:
        raise ValueError(f'No training image with the public id "{training_image_public_id}" exists')
    
    return query.filter_by(
        training_image=training_image
    )


@blueprint.route("/classified_areas", methods=['GET'])
def get_classified_areas():
    page = get_pagination_page()
    query = ClassifiedArea.query

    training_image_public_id = request.args.get("training_image")

    try:
        query = filter_by_training_image(query, training_image_public_id)
    except ValueError as e:
        return make_error_response(404, str(e))
    
    return jsonify(api_paginate_query(query, page=page, endpoint="api.get_classified_areas"))

@blueprint.route('/classified_areas/<string:public_id>', methods=['PUT'])
@login_required
def update_classified_area(current_user, public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()
    
    if not area.modifiable_by(current_user):
        return make_error_response(401, "Only admins can update other users classified_areas")
    
    try:
        area.update_attributes(request.json)
    except TypeError as e:
        return make_error_response(400, str(e))
    db.session.commit()

    return area.to_dict()



@blueprint.route("/classified_areas/<string:public_id>", methods=['GET'])
def get_classified_area(public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()
    return area.to_dict()

@blueprint.route("/classified_areas", methods=['POST'])
@login_required
def create_classified_area(current_user):
    data = request.get_json() or {}

    if 'training_image' not in data or 'x_position' not in data or 'y_position' not in data or 'width' not in data or 'height' not in data:
        return make_bad_request("training_image, x_position, y_position, width and height must be included")

    area = None
    try:
        area = ClassifiedArea.from_dict(data)
    except (ValueError, TypeError) as e:
        return make_bad_request(str(e))
    
    if not area.modifiable_by(current_user):
        return make_error_response(401, "You can only update your own classified_areas, only admins can update other users areas")
    
    db.session.add(area)
    db.session.commit()

    return jsonify(area.to_dict()), 201

@blueprint.route('/classified_areas/<string:public_id>/training_image_cropped')
def get_classified_area_image(public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()

    image = PIL.Image.open(area.training_image.get_image_path())
    
    image = image.crop(box=(
        area.x_position, area.y_position,
        area.x_position + area.width,
        area.y_position + area.height
    ))

    img_stream = io.BytesIO()
    image.save(img_stream, format="PNG")
    img_stream.seek(0)

    return send_file(img_stream, mimetype='image/png')

@blueprint.route('/classified_areas/<string:public_id>', methods=['DELETE'])
@login_required
def delete_classified_area(current_user, public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()

    if not area.modifiable_by(current_user):
        return make_bad_request(401, "You can only delete your own images since you are not an admin")
    
    db.session.delete(area)
    db.session.commit()

    return {"status": "success"}, 201

