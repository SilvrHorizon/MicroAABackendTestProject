from flask import Blueprint, jsonify, url_for, request
from werkzeug.http import HTTP_STATUS_CODES

from ..models import User, TrainingImage, api_paginate_query, ClassifiedArea

from app import db
from app.utilities import email_is_valid

#TODO REMOVE
from PIL import Image

api = Blueprint('api', __name__)

def get_pagination_page():
    page = request.args.get('page')
    if not page:
        page = 1
    else:
        try:
            page = int(page)
        except (ValueError):
            page = 1
    return page

def make_error_response(status_code, message=None):
    data = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')
    }

    if message:
        data["message"] = message
    
    response = jsonify(data)
    response.status_code = status_code
    return response

def make_bad_request(message=None):
    return make_error_response(status_code=400, message=message)

@api.route('/users/<string:public_id>', methods=['GET'])
def get_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()
    
    if user is not None: 
        return jsonify(user.to_dict())
    return make_error_response(404)

@api.route('/users', methods=["GET"])
def get_users():
    page = get_pagination_page()
    
    query = User.query
    return api_paginate_query(query, "api.get_users", page=page)

@api.route("/training_images/<string:public_id>", methods=['GET'])
def get_training_image(public_id):
    image = TrainingImage.query.file_type(public_id=public_id)
    if image:
        return image.to_dict()
    return make_error_response(404)

@api.route("/training_images", methods=['GET'])
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

@api.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}

    if 'email' not in data or 'password' not in data:
        return make_bad_request("Email and password must be included in create request")

    if not email_is_valid(data["email"]):
        return make_bad_request("Invalid email")

    if User.query.filter_by(email=data['email']).count() > 0:
        return make_bad_request("Email already in use")

    user = User.from_dict(data)
    db.session.add(user)
    db.session.commit()

    return user.to_dict(), 201


@api.route("/training_images", methods=['POST'])
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

@api.route("/classified_areas", methods=['GET'])
def get_classified_areas():
    page = get_pagination_page()

    query = ClassifiedArea.query
    return jsonify(api_paginate_query(query, page=page, endpoint="api.get_classified_areas"))

@api.route("/classified_areas/<string:public_id>", methods=['GET'])
def get_classified_area(public_id):
    area = ClassifiedArea.query.filter_by(public_id=public_id)
    
    if area:
        return area.to_dict()
    
    return make_error_response(404)

@api.route("/classified_areas", methods=['POST'])
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


