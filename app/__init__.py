from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config.from_object("app.config.Config")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app)

    # Register blueprints
    from .routes import main_routes

    app.register_blueprint(main_routes)

    return app
