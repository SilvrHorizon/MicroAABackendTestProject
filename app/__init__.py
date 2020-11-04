from flask import Flask
from app.extensions import db, migrate

from .api import blueprint as api_blueprint

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    # TEMPORARY
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///C:\\Users\\Jonat\\OneDrive\\Skrivbord\\MicroAABackendTestCase\\app.db'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app)

    app.register_blueprint(api_blueprint)
    #app.register_blueprint(site)

    return app
