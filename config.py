import os

basedir = os.path.abspath(os.path.dirname(__file__))

class DevelopmentConfig():
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "app.db")
    TRAINING_IMAGES_UPLOAD_URL = '/static/tests/training_images'
    TRAINING_IMAGES_UPLOAD_FOLDER = 'training_images'
    SECRET_KEY = "TEMPORARY"


class TestConfig():
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    TRAINING_IMAGES_UPLOAD_URL = '/static/tests/training_images'
    TRAINING_IMAGES_UPLOAD_FOLDER = os.path.join('tests', 'training_images')
    SECRET_KEY = "TEST"
