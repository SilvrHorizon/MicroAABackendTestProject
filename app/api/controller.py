from flask import Blueprint
from ..models import User, TrainingImage


api = Blueprint('api', __name__)

@api.route('/')
def get_user():
    return '<h2>Hello world this is a test!</h2>'