
import datetime
from flask import abort, current_app, jsonify, request
from functools import wraps
import jwt

from app import db
from app.models import User

from . import blueprint
from .errors import make_bad_request_response, make_error_response, make_unauthorized_response



def create_token(user):
    return jwt.encode(
        {
            "public_id": user.public_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(
                minutes=current_app.config["TOKEN_EXPIERY_IN_MINUTES"]
            )
        },
        current_app.config["SECRET_KEY"],
    )

@blueprint.route('/login')
def login():
    auth = request.authorization
    
    if not auth or not auth.username or not auth.password:
        return make_unauthorized_response("Missing credentials")
    
    user = User.query.filter_by(email=auth.username).first()
    if not user or not user.check_password(auth.password):
        return make_unauthorized_response("Invalid credentials")

    token = create_token(user)
    return jsonify({"x-access-token": token.decode('utf-8')})

def token_expired(decoded_token):
    return datetime.datetime.utcfromtimestamp(decoded_token['exp']) < datetime.datetime.utcnow() 

def decode_token_or_401():
    try:
        return jwt.decode(request.headers['x-access-token'], current_app.config["SECRET_KEY"])    
    except Exception:
        abort(401, "Invalid token")

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        decoded_token = decode_token_or_401()
        if token_expired(decoded_token):
            return make_unauthorized_response("Token expired")
        
        user = User.query.filter_by(public_id=decoded_token["public_id"]).first()
        if not user:
            return make_unauthorized_response("Invalid token")

        return f(user, *args, **kwargs)
    return decorated

# Route used to test authentication
@blueprint.route("/secret_protected_route")
@login_required
def test_auth_protection_route(current_user):
    return jsonify({"status": "success", "message": "wow you found a secret page!", "user": current_user.to_dict()}), 200