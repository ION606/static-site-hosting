from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .scheduler import scheduler

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object("app.config.Config")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Initialize scheduler
    from .scheduler import init_scheduler

    init_scheduler(app)

    # Register blueprints
    from .routes import main_routes

    app.register_blueprint(main_routes)

    return app
