from flask import Flask, jsonify
from flask_cors import CORS
import os
from routes.upload import upload_bp
from routes.rate import rate_bp
from routes.download import download_bp
from routes.retrieve import retrieve_bp
from routes.remove import remove_bp

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# confiure registry path
app.config["REGISTRY_PATH"] = REGISTRY_PATH
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(rate_bp)
app.register_blueprint(download_bp)
app.register_blueprint(retrieve_bp)
app.register_blueprint(remove_bp)


@app.route('/')
def home():
    return "Hello, Flask!"

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
    app.run(debug=True, port=5000)
