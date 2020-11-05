
import datetime
from functools import wraps
from flask import current_app, jsonify, g
import jwt

from app import db
from app.models import User

from . import blueprint, request
from .functions import make_error_response



def create_token(user):
    return jwt.encode({
        "public_id": user.public_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    },
    current_app.config["SECRET_KEY"])

@blueprint.route('/login')
def login():
    # TODO ADD www-authenticate header

    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_error_response(401, "Missing credentials")
    
    user = User.query.filter_by(email=auth.username).first()
    print("user", user)
    print("password", auth.password)
    if not user or not user.check_password(auth.password):
        return make_error_response(401, "Invalid credentials")

    token = create_token(user)

    return jsonify({"x-access-token": token.decode('utf-8')})


def login_required(f):
    # TODO better error messagges
    @wraps(f)
    def decorated(*args, **kwargs):
        global current_user
        decoded = None
        try:
            decoded = jwt.decode(request.headers['x-access-token'], current_app.config["SECRET_KEY"])    
        except Exception:
            return make_error_response(401, "Invalid token")

        if datetime.datetime.utcfromtimestamp(decoded['exp']) < datetime.datetime.utcnow():
            print(datetime.datetime.utcfromtimestamp(decoded['exp']))
            print(datetime.datetime.utcnow())
            return make_error_response(401, "Token expired")
        
        user = User.query.filter_by(public_id=decoded["public_id"]).first()
        if not user:
            return make_error_response(401, "Invalid token")

        return f(user, *args, **kwargs)
    return decorated
