from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import logging
from typing import cast
from routes.register import register_bp
from routes.rate import rate_bp
from routes.download import download_bp
from routes.retrieve import retrieve_bp
from routes.remove import remove_bp
from routes.health import health_bp
from routes.by_name import by_name_bp
from routes.put import put_bp

# paths
BASE_DIR = os.path.dirname(__file__)
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "../frontend/build")
REGISTRY_PATH = os.path.join(BASE_DIR, "registry.json")
LOG_FILE = os.path.join(BASE_DIR, "server.log")

logger = logging.getLogger("flask-app")

app = Flask(
    __name__,
    static_folder=FRONTEND_BUILD_DIR,  # serve built React files
    static_url_path=""
)
CORS(app)

# confiure registry path
app.config["REGISTRY_PATH"] = REGISTRY_PATH
app.config["API_KEY"] = os.getenv("API_KEY")

# Loggin setup
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# File handler (append mode)
file_handler = logging.FileHandler(LOG_FILE, mode="a")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
stream_handler.setFormatter(stream_formatter)

# Add both handlers (if not already added)
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

app.logger.handlers = logger.handlers
app.logger.setLevel(logging.DEBUG)


# Register blueprints
app.register_blueprint(register_bp)
app.register_blueprint(rate_bp)
app.register_blueprint(download_bp)
app.register_blueprint(retrieve_bp)
app.register_blueprint(remove_bp)
app.register_blueprint(health_bp)
app.register_blueprint(by_name_bp)
app.register_blueprint(put_bp)


# logging before request
@app.before_request
def log_request_info():
    logger.info(f"--->  {request.method} {request.path}")
    logger.debug(f"Headers: {dict(request.headers)}")
    if request.data:
        logger.debug(f"Body: {request.get_data(as_text=True)}")


# logging after request
@app.after_request
def log_response_info(response):
    logger.info(f"<---  {response.status} ({request.method} {request.path})")
    return response


# logging errors
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    logger.error(f"Unhandled exception: {e}\nTraceback:\n{tb}")
    return {"error": str(e)}, 500


@app.route("/tracks", methods=["GET"])
def get_track():
    output = {
        "plannedTracks": ["Performance track"]
    }

    if not output:
        return jsonify({"error": "Error retrieving tracks"}), 500

    return jsonify(output), 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    static_folder = cast(str, app.static_folder)  # tell Pylance it's not None

    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, "index.html")


# --- Entry Point ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
