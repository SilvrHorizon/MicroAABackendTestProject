from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash

import os

from app import db
from uuid import uuid4

from PIL import Image as PILImage
from PIL import UnidentifiedImageError


def generateUuid():
    return uuid4().hex

class User(db.Model):
    
    UPDATABLE_ATTRIBUTES = ['email', 'password', 'is_admin']
    ATTRIBUTE_TYPES = {
        'email': str,
        'password': str,
        'is_admin': bool
    }


    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)


    email = db.Column(db.String(248), index=True, nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    training_images = db.relationship("TrainingImage", backref="user", cascade="all,delete", lazy='dynamic')

    def __init__(self, email=None, password=None, is_admin=False):
        super()
        self.public_id = generateUuid()

        self.update_fields(
            dict(
                email=email,
                is_admin=is_admin,
                password=password,
            )
        )

    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)

    def check_password(self, to_check):
        return check_password_hash(self.password_hash, to_check)

    def to_dict(self):
        return {
            'email': self.email,
            'is_admin': self.is_admin,
            'public_id': self.public_id,
            '_links': {
                'self': url_for("api.get_user", public_id=self.public_id),
                'training_images': url_for("api.get_training_images", user=self.public_id)
            }
        }

    def update_fields(self, data):
        User.validate_argument_types(data)

        for field in data:
            if field in User.UPDATABLE_ATTRIBUTES:
                setattr(self, field, data[field])
        
        if 'password' in data:
            self.set_password(data['password'])

    @staticmethod
    def validate_argument_types(dictionary):
        for field in dictionary:
            if field in User.UPDATABLE_ATTRIBUTES:
                if not isinstance(dictionary[field], User.ATTRIBUTE_TYPES[field]):
                    raise TypeError(f'{field} was of type {type(dictionary[field]).__name__} not of type {User.ATTRIBUTE_TYPES[field].__name__}')

    @staticmethod
    def from_dict(dictionary):
        user = User(**dictionary) 
        return user
    
    def modifiable_by(self, user):
        return self == user or user.is_admin



class TrainingImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'),)

    classified_areas = db.relationship("ClassifiedArea", cascade="all,delete", backref="training_images", lazy='dynamic')

    def set_image(self, im_stream):
        try:
            image = PILImage.open(im_stream)
        except UnidentifiedImageError:
            raise ValueError('Image file passed is corrupt/not an image')
        
        image.save(os.path.join(current_app.static_folder, current_app.config['TRAINING_IMAGES_UPLOAD_FOLDER'], f'{self.public_id}.png'))
        self.width, self.height = image.size
    
    def modifiable_by(self, user):
        return self.user == user or user.is_admin

        
    def delete_image(self):
        if os.path.exists(self.get_image_path()):
            os.remove(self.get_image_path())

    def __init__(self, user):
        self.public_id = generateUuid()
        if user is None:
            raise ValueError("User does not exist, please pass a valid user")
        self.user = user

    @staticmethod
    def from_dict(dictionary):
        return TrainingImage(user=User.query.filter_by(public_id=dictionary["user"]).first())

    def get_image_url(self):
        return current_app.config["TRAINING_IMAGES_UPLOAD_URL"] + f'/{self.public_id}.png'

    def get_image_path(self):
        return os.path.join(current_app.static_folder, current_app.config['TRAINING_IMAGES_UPLOAD_FOLDER'], f'{self.public_id}.png')


    classified_areas = db.relationship("ClassifiedArea", backref="training_image", lazy='dynamic')
    
    def to_dict(self):
        return {
            "public_id": self.public_id,
            "image_url": self.get_image_url(),
            "width": self.width,
            "height": self.height,
            
            "user": self.user.public_id,
            
            "_links": {
                "self": url_for("api.get_training_image", public_id=self.public_id),
                "user": url_for("api.get_user", public_id=self.user.public_id),
                "classified_areas": url_for('api.get_classified_areas', training_image=self.public_id)
            }
        }


class ClassifiedArea(db.Model):
    UPDATABLE_ATTRIBUTES = ['x_position', 'y_position', 'width', 'height', 'tag', 'training_image']
    ATTRIBUTE_TYPES = {
        'x_position': int, 
        'y_position': int,
        'width': int,
        'height': int,
        'tag': (str, type(None)),
        'training_image': (TrainingImage, str)
    }


    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    tag = db.Column(db.String(256), index=True)
    image_id = db.Column(db.Integer, db.ForeignKey(f'{TrainingImage.__tablename__}.id'))

    x_position = db.Column(db.Integer)
    y_position = db.Column(db.Integer)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    def modifiable_by(self, user):
        return self.training_image.user == user or user.is_admin

    def to_dict(self):
        return {
            "x_position": self.x_position,
            "y_position": self.y_position,

            "width": self.width,
            "height": self.height,

            "tag": self.tag,

            "public_id": self.public_id,

            "training_image": self.training_image.public_id,

            "_links": {
                "self": url_for("api.get_classified_area", public_id=self.public_id),
                "training_image": url_for(
                    "api.get_training_image", public_id=self.training_image.public_id
                ) if self.training_image else None
            }
        }

    def __init__(self, x_position, y_position, width, height, training_image, tag=None):
        self.update_attributes(
            dict(
                x_position=x_position,
                y_position=y_position,

                width=width,
                height=height,

                tag=tag,
                training_image=training_image
            )

        )


        self.x_position = x_position
        self.y_position = y_position

        self.width = width
        self.height = height
        self.training_image = training_image
        
        self.tag = tag.lower() if tag else None

    @staticmethod
    def validate_arguments(arguments):
        ClassifiedArea.validate_argument_types(arguments)
        ClassifiedArea.validate_argument_values(arguments)

    @staticmethod
    def validate_argument_types(arguments):
        for field in arguments:
            if field in ClassifiedArea.UPDATABLE_ATTRIBUTES:
                if not isinstance(arguments[field], ClassifiedArea.ATTRIBUTE_TYPES[field]):
                    if isinstance(ClassifiedArea.ATTRIBUTE_TYPES[field], tuple):
                        raise TypeError(f'{field} was of type {type(arguments[field]).__name__} not of type {list(i.__name__ for i in ClassifiedArea.ATTRIBUTE_TYPES[field])}') 
                    else:
                        raise TypeError(f'{field} was of type {type(arguments[field]).__name__} not of type {ClassifiedArea.ATTRIBUTE_TYPES[field].__name__}') 
                

    @staticmethod
    def validate_argument_values(arguments): 
        if arguments['x_position'] < 0 or arguments['y_position'] < 0:
            raise ValueError("ClassifiedAreas cannot extend out of the bounds the parent image!")
        
        if arguments['x_position'] + arguments['width'] > arguments['training_image'].width or arguments['y_position'] + arguments['height'] > arguments['training_image'].height:
            raise ValueError("ClassifiedAreas cannot extend out of the bounds the parent image!")

        if arguments['width'] < 0 or arguments['height'] < 0:
            raise ValueError("Width and height cannot be below 0")

    @staticmethod
    def convert_traning_image_to_object_if_string(dictionary):
        if isinstance(dictionary['training_image'], str):
            dictionary['training_image'] = TrainingImage.query.filter_by(public_id=dictionary['training_image']).first()
        
        if not dictionary['training_image']:
            raise ValueError("Passed traning image does not exist")

    def update_attributes(self, dictionary):
        self.convert_traning_image_to_object_if_string(dictionary)
        self.validate_arguments(dictionary)

        for field in dictionary:
            if field in ClassifiedArea.UPDATABLE_ATTRIBUTES:
                setattr(self, field, dictionary[field])


    @staticmethod
    def from_dict(data):
        data['training_image'] = TrainingImage.query.filter_by(public_id=data["training_image"]).first()
        area = ClassifiedArea(
            **data
        )
        return area
