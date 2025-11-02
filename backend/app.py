from flask import Flask, jsonify
from flask_cors import CORS
import os
from routes.register import register_bp
from routes.rate import rate_bp
from routes.download import download_bp
from routes.retrieve import retrieve_bp
from routes.remove import remove_bp
from routes.health import health_bp

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")

# Initialize Flask app
app = Flask(__name__)
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

@app.route('/')
def home():
    return "Hello, Flask! Testing deployment to AWS"


@app.route('/tracks', methods=['GET'])
def get_track():
    output = {
        "plannedTracks": [
            "Performance track"
        ]
    }

    # Simulate error somehow with 500 status error
    if not output:
        return jsonify({"error": "Error with getting track"}), 500

    return jsonify(output), 200


if __name__ == "__main__":
    # app.run(debug=True, port=5000)

    app.run(host="0.0.0.0", port=5000, debug=False)
