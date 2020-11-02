from flask import Flask
from app.extensions import db, migrate

from .api.controller import api

from .testbp import site

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    migrate.init_app(app)

    app.register_blueprint(api)
    #app.register_blueprint(site)

    return app
