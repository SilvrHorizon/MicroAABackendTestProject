from dotenv import load_dotenv
import os


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class DevelopmentConfig(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///' + os.path.join(basedir, "app.db")
    
    TRAINING_IMAGES_UPLOAD_URL = os.environ.get('TRAINING_IMAGES_UPLOAD_URL') or '/static/training_images'
    TRAINING_IMAGES_UPLOAD_FOLDER = os.environ.get('TRAINING_IMAGES_UPLOAD_FOLDER') or 'training_images'
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or "TEMPORARY"

    TOKEN_EXPIERY_IN_MINUTES = int(os.environ.get('TOKEN_EXPIERY_IN_MINUTES')) if os.environ.get('TOKEN_EXPIERY_IN_MINUTES') else 12 * 60
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE')) if os.environ.get('ITEMS_PER_PAGE') else 12 * 60


class TestConfig(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    TRAINING_IMAGES_UPLOAD_URL = '/static/tests/training_images'
    TRAINING_IMAGES_UPLOAD_FOLDER = os.path.join('tests', 'training_images')
    SECRET_KEY = "TEST"
    TOKEN_EXPIERY_IN_MINUTES = 12 * 60
    ITEMS_PER_PAGE = 10
