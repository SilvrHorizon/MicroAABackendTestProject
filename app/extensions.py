from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate(db=db)

def register_app(app):
    db.init_app(app)
    migrate.init_app(app)
