"""Flask application factory for the ACEest Fitness classroom adaptation."""
import os
from pathlib import Path
from flask import Flask
from .database import init_db, close_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "ACEEST_DB_PATH", str(Path(app.instance_path) / "aceest.sqlite3")
        ),
        JSON_SORT_KEYS=False,
    )
    if test_config is not None:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        init_db()

    app.teardown_appcontext(close_db)

    from .routes import bp
    app.register_blueprint(bp)
    return app
