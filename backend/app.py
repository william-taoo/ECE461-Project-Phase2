from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
from typing import cast
from routes.register import register_bp
from routes.rate import rate_bp
from routes.download import download_bp
from routes.retrieve import retrieve_bp
from routes.remove import remove_bp
from routes.health import health_bp

# paths
BASE_DIR = os.path.dirname(__file__)
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "../frontend/build")
REGISTRY_PATH = os.path.join(BASE_DIR, "registry.json")

app = Flask(
    __name__,
    static_folder=FRONTEND_BUILD_DIR,  # serve built React files
    static_url_path="/"
)
CORS(app)

# confiure registry path
app.config["REGISTRY_PATH"] = REGISTRY_PATH
app.config["API_KEY"] = os.getenv("API_KEY")

# Register blueprints
app.register_blueprint(register_bp)
app.register_blueprint(rate_bp)
app.register_blueprint(download_bp)
app.register_blueprint(retrieve_bp)
app.register_blueprint(remove_bp)
app.register_blueprint(health_bp)


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
