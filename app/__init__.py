from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

# 🔥 Single DB instance (VERY IMPORTANT)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Secret key
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    # Database URL
    database_url = os.environ.get('DATABASE_URL')

    # Fix Render postgres:// issue
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

    # Import models AFTER db init
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)  # UUID safe

    # Register routes
    from app.routes import main
    app.register_blueprint(main)

    # Auto create tables (for MVP simplicity)
    with app.app_context():
        db.create_all()

    return app
