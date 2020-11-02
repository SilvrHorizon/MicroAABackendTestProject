from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from uuid import uuid4


def generateUuid():
    return uuid4().hex

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)


    email = db.Column(db.String(248), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    
    is_admin = db.Column(db.Boolean)
    
    training_images = db.relationship("TrainingImage", backref="user", lazy='dynamic')

    def __init__(self, email="only", password_plain="for test purpose", is_admin=False):
        super()

        self.email = email
        self.public_id = generateUuid()

        self.set_password(password_plain)

    def set_password(self, password_plain):
        self.password_hash = generate_password_hash(password_plain)

    def check_password(self, to_check):
        return check_password_hash(self.password_hash, to_check)


class TrainingImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey(f'{User.__tablename__}.id'),)
    
    def __init__(self, user):
        self.public_id = generateUuid()
        self.user = user

    def get_image_url(self):
        return current_app.config["TRAINING_IMAGE_UPLOAD_URL"] + f'/{self.public_id}'

    classified_areas = db.relationship("ClassifiedArea", backref="image", lazy='dynamic')


    def accessible_by(self, user):
        return self.user_id == user.id or user.is_admin


class ClassifiedArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), unique=True, default=generateUuid, index=True)

    classified_as = db.Column(db.String(256), index=True)
    image_id = db.Column(db.Integer, db.ForeignKey(f'{TrainingImage.__tablename__}.id'))

    x_position = db.Column(db.Integer)
    y_position = db.Column(db.Integer)

    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    def accessible_by(self, user):
        return self.image.accessible_by(user)



    
