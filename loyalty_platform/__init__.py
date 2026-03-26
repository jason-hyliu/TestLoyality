import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from loyalty_platform.extensions import db, migrate


def create_app(config=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, "loyalty.db")
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key"))

    if config:
        app.config.update(config)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from loyalty_platform.api import (
        members_bp,
        tiers_bp,
        activities_bp,
        campaigns_bp,
        rewards_bp,
        analytics_bp,
    )

    app.register_blueprint(members_bp)
    app.register_blueprint(tiers_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(campaigns_bp)
    app.register_blueprint(rewards_bp)
    app.register_blueprint(analytics_bp)

    # Serve the frontend SPA
    @app.route("/")
    @app.route("/<path:path>")
    def frontend(path=""):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.template_folder, "index.html")

    # Initialize DB tables and seed data on first run
    with app.app_context():
        db.create_all()
        from loyalty_platform.seed import seed_all
        seed_all()

    return app
