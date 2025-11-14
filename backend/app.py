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

app = Flask(
    __name__,
    static_folder=FRONTEND_BUILD_DIR,
    static_url_path=""
)
CORS(app)

# confiure registry path
app.config["REGISTRY_PATH"] = REGISTRY_PATH
app.config["API_KEY"] = os.getenv("API_KEY")

# logging setup
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logger = logging.getLogger("flask-app")
logger.setLevel(logging.DEBUG)

# file handler (append mode)
file_handler = logging.FileHandler(LOG_FILE, mode="a")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

# ensure Flask uses our logger
app.logger.handlers = logger.handlers
app.logger.setLevel(logging.DEBUG)

# register blueprints
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
    logger.info(f"-------->  {request.method} {request.path}?{request.query_string.decode()}")
    logger.debug(f"Headers: {dict(request.headers)}")

    if request.data:
        body_text = request.get_data(as_text=True)
        if len(body_text) > 1000:
            body_text = body_text[:1000] + "... [truncated]"
        logger.debug(f"Body: {body_text}")


# logging after request
@app.after_request
def log_response_info(response):
    logger.info(f"<--------  {response.status} ({request.method} {request.path})")
    logger.debug(f"Response headers: {dict(response.headers)}")

    if not response.direct_passthrough and response.data:
        resp_text = response.get_data(as_text=True)
        if len(resp_text) > 1000:
            resp_text = resp_text[:1000] + "... [truncated]"
        logger.debug(f"Response body: {resp_text}")

    return response


# error logging
@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    tb = traceback.format_exc()
    logger.error(f"Unhandled exception: {e}\nTraceback:\n{tb}")
    return {"error": str(e)}, 500


# routes
@app.route("/tracks", methods=["GET"])
def get_track():
    output = {"plannedTracks": ["Performance track"]}
    return jsonify(output), 200


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    static_folder = cast(str, app.static_folder)
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    return send_from_directory(static_folder, "index.html")


# entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
