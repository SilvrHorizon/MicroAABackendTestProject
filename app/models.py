from flask import current_app, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import os

from app import db
from PIL import Image as PILImage, UnidentifiedImageError
from uuid import uuid4

from .utilities import valid_email, valid_password


def generateUuid():
    return uuid4().hex

class APIModelMixin(object):
    @classmethod
    def raise_invalid_argument_type_exception(cls, arguments, argument):
        if isinstance(cls.ATTRIBUTE_TYPES[argument], tuple):
            raise TypeError(f'{argument} was of type {type(arguments[argument]).__name__} not of type {list(i.__name__ for i in cls.ATTRIBUTE_TYPES[argument])}') 
        else:
            raise TypeError(f'{argument} was of type {type(arguments[argument]).__name__} not of type {cls.ATTRIBUTE_TYPES[argument].__name__}')   

    @classmethod
    def validate_argument_types(cls, arguments):
        for argument in arguments:
            if argument in cls.UPDATABLE_ATTRIBUTES:
                if not isinstance(arguments[argument], cls.ATTRIBUTE_TYPES[argument]):
                    cls.raise_invalid_argument_type_exception(arguments, argument)
    
    @classmethod
    def from_dict(cls, dictionary):
        return cls(**dictionary)


    @classmethod
    def validate_argument_values(cls, arguments):
        pass

    @classmethod
    def validate_arguments(cls, arguments):
        cls.validate_argument_types(arguments)
        cls.validate_argument_values(arguments)

    def update_attributes(self, arguments):
        pass

    def modifiable_by(self, user):
        pass

    def to_dict(self):
        pass


        
        


class User(db.Model, APIModelMixin):
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

    def __init__(self, **kwargs):
        super()
        self.public_id = generateUuid()

        self.update_attributes(
            kwargs
        )

    def update_attributes(self, data):
        User.validate_arguments(data)
        for field in data:
            if field in User.UPDATABLE_ATTRIBUTES:
                if field == 'password':
                    self.set_password(data['password'])
                else:
                    setattr(self, field, data[field])
    
    def to_dict(self):
        return {
            'email': self.email,
            'is_admin': self.is_admin,
            'public_id': self.public_id,
            '_links': {
                'self': url_for("api.get_user", public_id=self.public_id),
                'training_images': url_for("api.get_training_images", user=self.public_id),
                'promote': url_for('api.promote_user', public_id=self.public_id),
                'demote': url_for('api.demote_user', public_id=self.public_id)
            }
        }

    def modifiable_by(self, user):
        return self == user or user.is_admin
    
    def check_password(self, to_check):
        return check_password_hash(self.password_hash, to_check)
    
    def set_password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)
    
    @classmethod
    def validate_argument_values(cls, dictionary):
        if 'email' in dictionary:
            if not valid_email(dictionary["email"]):
                raise ValueError("Invalid email address!")
        
        if 'password' in dictionary:
            if not valid_password(dictionary['password']):
                raise ValueError("Invalid password!")



class TrainingImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'),)

    classified_areas = db.relationship("ClassifiedArea", cascade="all,delete", backref="training_image", lazy='dynamic')
    
    def __init__(self, user):
        self.public_id = generateUuid()
        if user is None:
            raise ValueError("User does not exist, please pass a valid user")
        self.user = user
    
    def to_dict(self):
        return {
            "public_id": self.public_id,
            "width": self.width,
            "height": self.height,
            
            "user": self.user.public_id,
            
            "_links": {
                "image": self.get_image_url(),
                "self": url_for("api.get_training_image", public_id=self.public_id),
                "user": url_for("api.get_user", public_id=self.user.public_id),
                "classified_areas": url_for('api.get_classified_areas', training_image=self.public_id)
            }
        }
    
    def modifiable_by(self, user):
        return self.user == user or user.is_admin
    
    def set_image(self, im_stream):
        self.delete_image()  # Remove any existing image ( if there is one)

        try:
            image = PILImage.open(im_stream)
        except UnidentifiedImageError:
            raise ValueError('Image file passed is corrupt/not an image')
        
        image.save(os.path.join(current_app.static_folder, current_app.config['TRAINING_IMAGES_UPLOAD_FOLDER'], f'{self.public_id}.png'))
        self.width, self.height = image.size
        
    def delete_image(self):
        if os.path.exists(self.get_image_path()):
            os.remove(self.get_image_path())


    @staticmethod
    def from_dict(dictionary):
        return TrainingImage(user=User.query.filter_by(public_id=dictionary["user"]).first())

    def get_image_url(self):
        return current_app.config["TRAINING_IMAGES_UPLOAD_URL"] + f'/{self.public_id}.png'

    def get_image_path(self):
        return os.path.join(current_app.static_folder, current_app.config['TRAINING_IMAGES_UPLOAD_FOLDER'], f'{self.public_id}.png')


    
def convert_to_traning_image_object_if_string(training_image):
    if isinstance(training_image, str):
        training_image = TrainingImage.query.filter_by(public_id=training_image).first()
    
    if training_image is None:
        raise ValueError("Passed traning image does not exist")

    return training_image

class ClassifiedArea(db.Model, APIModelMixin):
    UPDATABLE_ATTRIBUTES = ['x_position', 'y_position', 'width', 'height', 'tag', 'training_image']
    ATTRIBUTE_TYPES = {
        'x_position': int, 
        'y_position': int,
        'width': int,
        'height': int,
        'tag': (str, type(None)),
        'training_image': (TrainingImage)
    }


    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    tag = db.Column(db.String(256), index=True)

    x_position = db.Column(db.Integer)
    y_position = db.Column(db.Integer)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    image_id = db.Column(db.Integer, db.ForeignKey(f'{TrainingImage.__tablename__}.id'))
    
    def __init__(self, **kwargs):
        
        self.update_attributes(
            kwargs
        )

    def update_attributes(self, dictionary):
        self.prepare_dictionary_of_attributes(dictionary)

        for field in dictionary:
            if field in ClassifiedArea.UPDATABLE_ATTRIBUTES:
                setattr(self, field, dictionary[field])

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
                ) if self.training_image else None,
                "training_image_cropped": url_for(
                    "api.get_classified_area_image", public_id=self.public_id
                )
            }
        }

    def modifiable_by(self, user):
        return self.training_image.user == user or user.is_admin


    def prepare_dictionary_of_attributes(self, dictionary):
        self.fill_missing_attributes(dictionary)
        
        # Make training_image of correct type
        dictionary['training_image'] = convert_to_traning_image_object_if_string(dictionary['training_image'])
        
        # Tag can be of none type
        if dictionary['tag']:
            dictionary['tag'] = dictionary['tag'].lower()
        
        self.validate_arguments(dictionary)

    def fill_missing_attributes(self, dictionary):
        for attribute in ClassifiedArea.UPDATABLE_ATTRIBUTES:
            if attribute not in dictionary:
                dictionary[attribute] = getattr(self, attribute)

    @classmethod
    def validate_argument_values(cls, arguments): 
        if arguments['x_position'] < 0 or arguments['y_position'] < 0:
            raise ValueError("ClassifiedAreas cannot extend out of the bounds the parent image!")
        
        if arguments['x_position'] + arguments['width'] > arguments['training_image'].width or arguments['y_position'] + arguments['height'] > arguments['training_image'].height:
            raise ValueError("ClassifiedAreas cannot extend out of the bounds the parent image!")

        if arguments['width'] < 1 or arguments['height'] < 1:
            raise ValueError("Width and height cannot be below 1px")
