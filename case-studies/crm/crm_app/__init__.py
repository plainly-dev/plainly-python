"""A small CRM: contacts, notes and a sales pipeline."""

from flask import Flask, jsonify, request

from .store import ContactStore
from .views import api, pages


def create_app(test_config=None):
    """Build a new CRM with its own empty storage."""
    app = Flask(__name__)
    app.config.update(SECRET_KEY="dev-only-change-me")
    if test_config:
        app.config.update(test_config)

    app.extensions["contacts"] = ContactStore()
    app.register_blueprint(pages)
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify(error="Contact not found" if request.path != "/api/" else "Not found"), 404
        return error

    return app
