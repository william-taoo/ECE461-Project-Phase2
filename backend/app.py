from flask import Flask
from flask_cors import CORS
import os
from routes.upload import upload_bp 
from routes.rate import rate_bp
from routes.download import download_bp
from routes.retrieve import retrieve_bp

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(rate_bp)
app.register_blueprint(download_bp)
app.register_blueprint(retrieve_bp)

@app.route('/')
def home():
    return "Hello, Flask!"


if __name__ == "__main__":
    app.run(debug=True, port=5000)