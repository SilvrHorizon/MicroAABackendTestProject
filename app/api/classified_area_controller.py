from flask import abort, current_app, jsonify, request, send_file

import io
import PIL

from app import db
from app.models import ClassifiedArea, TrainingImage


from . import blueprint
from .errors import make_error_response, make_bad_request_response, make_unauthorized_response
from .pagination import api_paginate_query, get_pagination_page



from .auth import login_required


# Partially bad name, read function for better understanding 
def filter_by_training_image_or_404(query, training_image_public_id):
    
    # If there is no specific training image to filter by, return the query as it is
    if training_image_public_id is None:
        return query
    
    training_image = TrainingImage.query.filter_by(public_id=training_image_public_id).first()
    
    if not training_image:
        abort(404, f'No training image with the public id "{training_image_public_id}" exists')
    
    return query.filter_by(
        training_image=training_image
    )

# Partially bad name, read function for better understanding 
def filter_by_tag(query, tag):
    if tag is None:
        return query

    return query.filter_by(
        tag=tag
    )


@blueprint.route("/classified_areas", methods=['GET'])
def get_classified_areas():
    page = get_pagination_page()
    query = ClassifiedArea.query

    training_image_public_id = request.args.get("training_image")
    tag_filter = request.args.get("tag")


    query = filter_by_training_image_or_404(query, training_image_public_id)
    query = filter_by_tag(query, tag_filter)

    return jsonify(api_paginate_query(query, page=page, per_page=current_app.config["ITEMS_PER_PAGE"], endpoint="api.get_classified_areas", tag=tag_filter, training_image=training_image_public_id))

@blueprint.route('/classified_areas/<string:public_id>', methods=['PUT'])
@login_required
def update_classified_area(current_user, public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()
    
    if not area.modifiable_by(current_user):
        return make_unauthorized_response("Only admins can update other users classified_areas")
    
    try:
        area.update_attributes(request.json)
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return make_bad_request_response(str(e))
    
    db.session.commit()
    return area.to_dict()



@blueprint.route("/classified_areas/<string:public_id>", methods=['GET'])
def get_classified_area(public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id).first_or_404()
    return area.to_dict()


def abort_if_missing_fields(data):
    if 'training_image' not in data or 'x_position' not in data or 'y_position' not in data or 'width' not in data or 'height' not in data:
        abort(400, "training_image, x_position, y_position, width and height must be included") 


@blueprint.route("/classified_areas", methods=['POST'])
@login_required
def create_classified_area(current_user):
    data = request.get_json() or {}

    abort_if_missing_fields(data)

    area = None
    try:
        area = ClassifiedArea.from_dict(data)
    except (ValueError, TypeError) as e:
        return make_bad_request_response(str(e))
    
    if not area.modifiable_by(current_user):
        return make_unauthorized_response("You can only update your own classified_areas, only admins can update other users areas")
    
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
        return make_unauthorized_response(401, "You can only delete your own images since you are not an admin")

    db.session.delete(area)
    db.session.commit()

    return {"status": "success"}, 201

