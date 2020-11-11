from flask import Flask

from .extensions import db, migrate, register_app as register_app_to_extensions
from config import DevelopmentConfig

def register_blueprints(app):
    from .api import blueprint as api_blueprint
    app.register_blueprint(api_blueprint)

    from .errors import blueprint as errors_blueprint
    app.register_blueprint(errors_blueprint)


def create_app(config=DevelopmentConfig()):
    app = Flask(__name__)

    app.config.from_object(config)
    register_app_to_extensions(app)
    register_blueprints(app)
    
    return app
