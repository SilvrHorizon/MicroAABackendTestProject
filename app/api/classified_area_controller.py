from flask import jsonify, request, send_file

import io
import PIL

from app import db
from app.models import ClassifiedArea, TrainingImage


from . import blueprint
from .functions import api_paginate_query, get_pagination_page, make_bad_request, make_error_response

from .auth import login_required

@blueprint.route("/classified_areas", methods=['GET'])
def get_classified_areas():
    page = get_pagination_page()
    query = ClassifiedArea.query

    training_image_public_id = request.args.get("training_image")
    if training_image_public_id:
        training_image = TrainingImage.query.filter_by(public_id=training_image_public_id).first()
        if training_image:
            query = query.filter_by(training_image=training_image)
        else:
            return make_bad_request(f'No training image with id: {training_image_public_id} exists')
    
    return jsonify(api_paginate_query(query, page=page, endpoint="api.get_classified_areas"))

@blueprint.route('/classified_areas/<string:public_id>', methods=['PUT'])
@login_required
def update_classified_area(current_user, public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()
    
    if area.training_image.user != current_user and not current_user.is_admin:
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

# TODO Authorization for POST
@blueprint.route("/classified_areas", methods=['POST'])
def create_classified_area():
    data = request.get_json() or {}

    if 'training_image' not in data or 'x_position' not in data or 'y_position' not in data or 'width' not in data or 'height' not in data:
        return make_bad_request("training_image, x_position, y_position, width and height must be included")

    area = None
    
    try:
        area = ClassifiedArea.from_dict(data)
    except (ValueError, TypeError) as e:
        return make_bad_request(str(e))
    db.session.add(area)
    db.session.commit()

    return jsonify(area.to_dict()), 201

@blueprint.route('/classified_areas/<public_id>/training_image_cropped')
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



