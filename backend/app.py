from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from routes.upload import upload_bp 
from routes.rate import rate_bp
from routes.download import download_bp


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(rate_bp)
app.register_blueprint(download_bp)
