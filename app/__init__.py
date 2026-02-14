from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.models import db, User   # ✅ import db from models (IMPORTANT)

load_dotenv()

login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Database URL
    database_url = os.environ.get('DATABASE_URL')

    # Fix for Render postgres:// issue
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'

    # ✅ Correct user loader (UUID STRING, NOT INT)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    from app.routes import main
    app.register_blueprint(main)

    # ✅ CREATE TABLES IF THEY DON'T EXIST
    with app.app_context():
        db.create_all()

    return app
