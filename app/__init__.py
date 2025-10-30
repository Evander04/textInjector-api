from flask import Flask
import os
from app.extensions import db, migrate
from flask_cors import CORS

def create_app():
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 20 MB
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    
    # CORS SETUP
    CORS(
    app,
    resources={r"/api/*": {"origins": ["*"]}},
    supports_credentials=False,                    # set True only if using cookies
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=86400,
    )


    app_env = os.getenv("APP_ENV", "development").lower()
    config_map = {
        "development": "app.config.dev.DevConfig",
        "production": "app.config.prod.ProdConfig",
    }
    app.config.from_object(config_map.get(app_env, "app.config.dev.DevConfig"))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints    
    from app.controllers.users import users_bp
    from app.controllers.extract import extract_bp
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(extract_bp, url_prefix="/api/extract")

    return app
