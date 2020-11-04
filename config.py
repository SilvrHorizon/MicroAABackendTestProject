import os

basedir = os.path.abspath(os.path.dirname(__file__))

class DevelopmentConfig():
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "app.db")
    TRAINING_IMAGE_UPLOAD_URL = '/static/training_images'
    SECRET_KEY = "TEMPORARY"


class TestConfig():
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    TRAINING_IMAGE_UPLOAD_URL = '/static/training_images'
    SECRET_KEY = "TEST"
