from flask import jsonify, request

from app.models import ClassifiedArea

from . import blueprint
from .functions import api_paginate_query, get_pagination_page, make_bad_request, make_error_response


@blueprint.route("/classified_areas", methods=['GET'])
def get_classified_areas():
    page = get_pagination_page()

    query = ClassifiedArea.query
    return jsonify(api_paginate_query(query, page=page, endpoint="api.get_classified_areas"))

@blueprint.route("/classified_areas/<string:public_id>", methods=['GET'])
def get_classified_area(public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id)

    if area:
        return area.to_dict()

    return make_error_response(404)

@blueprint.route("/classified_areas", methods=['POST'])
def create_classified_area():
    data = request.get_json() or {}

    if 'training_image' not in data or 'x_position' not in data or 'y_position' not in data or 'width' not in data \
            or 'height' not in data or 'y_position' not in data:
        return make_bad_request("Training image, x_position, y_position, widht and height must be included")

    try:
        area = ClassifiedArea.from_dict(data)
        return jsonify(area.to_dict()), 201
    except ValueError as e:
        return make_bad_request(str(e))
