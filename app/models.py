from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash

import os

from app import db
from uuid import uuid4

from PIL import Image as PILImage


def generateUuid():
    return uuid4().hex

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)


    email = db.Column(db.String(248), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    training_images = db.relationship("TrainingImage", backref="user", lazy='dynamic')

    def __init__(self, email="only", password_plain="for test purpose", is_admin=False):
        super()
        self.email = email
        self.public_id = generateUuid()
        self.is_admin = is_admin

        self.set_password(password_plain)

    def set_password(self, password_plain):
        self.password_hash = generate_password_hash(password_plain)

    def check_password(self, to_check):
        return check_password_hash(self.password_hash, to_check)

    def to_dict(self):
        return {
            'email': self.email,
            'is_admin': self.is_admin,
            'public_id': self.public_id,
            '_links': {
                'this': url_for("api.get_user", public_id=self.public_id),
                'training_images': url_for("api.get_training_images", user=self.public_id)
            }
        }
    
    @staticmethod
    def from_dict(dictionary):
        
        return User(
            email=dictionary["email"],
            password_plain=dictionary["password"],
            is_admin=dictionary["is_admin"] if "is_admin" in dictionary else False
        )


class TrainingImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'),)

    classified_areas = db.relationship("ClassifiedArea", backref="training_images", lazy='dynamic')

    def set_image(self, im_stream):
        image = PILImage.open(im_stream)
        image.save(os.path.join(current_app.static_folder, 'training_images', f'{self.public_id}.png'))

    def __init__(self, user):
        self.public_id = generateUuid()
        if user is None:
            raise ValueError("User does not exist, please pass a valid user")
        self.user = user

    @staticmethod
    def from_dict(dictionary):
        return TrainingImage(user=User.query.filter_by(public_id=dictionary["user"]).first())

    def get_image_url(self):
        return current_app.config["TRAINING_IMAGE_UPLOAD_URL"] + f'/{self.public_id}.png'

    classified_areas = db.relationship("ClassifiedArea", backref="training_image", lazy='dynamic')

    def accessible_by(self, user):
        return self.user_id == user.id or user.is_admin
    
    def to_dict(self):
        return {
            "public_id": self.public_id,
            "image_url": self.get_image_url(),
            "_links": {
                "self": url_for("api.get_training_image", public_id=self.public_id),
                "user": url_for("api.get_user", public_id=self.user.public_id),
                "classified_areas": url_for('api.get_classified_areas', training_image=self.public_id)
            }
        }


class ClassifiedArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    tag = db.Column(db.String(256), index=True)
    image_id = db.Column(db.Integer, db.ForeignKey(f'{TrainingImage.__tablename__}.id'))

    x_position = db.Column(db.Integer)
    y_position = db.Column(db.Integer)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    def to_dict(self):
        return {
            "x_position": self.x_position,
            "y_position": self.y_position,

            "width": self.width,
            "height": self.height,

            "tag": self.tag,

            "_links": {
                "self": url_for("api.get_classified_area", public_id=self.public_id),
                "training_image": url_for(
                    "api.get_training_image", public_id=self.training_image.public_id
                ) if self.training_image else None
            }
        }

    def __init__(self, x_position, y_position, width, height, training_image, tag=None):
        if not training_image: 
            raise ValueError("Passed TrainingImage does not exist")

        self.x_position = x_position
        self.y_position = y_position

        self.width = width
        self.height = height
        self.training_image = training_image



    def accessible_by(self, user):
        return self.image.accessible_by(user)

    @staticmethod
    def from_dict(data):
        print("Training image public_id", data["training_image"])

        area = ClassifiedArea(
            x_position=data["x_position"],
            y_position=data["y_position"],

            width=data["width"],
            height=data["height"],
            training_image=TrainingImage.query.filter_by(public_id=data["training_image"]).first()
        )
        return area
