from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_mapping(
        SECRET_KEY="dev-secret-key",
        MAX_CONTENT_LENGTH=102 * 1024 * 1024,
        UPLOAD_FOLDER="tmp_uploads",
        SESSION_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_HTTPONLY=True,
    )

    from app.routes import bp as routes_bp

    app.register_blueprint(routes_bp)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_upload_too_large(error):
        return jsonify(
            {
                "accepted": False,
                "status": "UPLOAD_TOO_LARGE",
                "alert": "Upload exceeds the maximum allowed size.",
                "message": "Upload exceeds the maximum allowed size.",
            }
        ), 413

    return app
