from flask import Flask
from flask_cors import CORS  # Add this import
from routes.contact import contact_bp
from routes.chatbot import chatbot_bp
from utils.resume_utils import upload_portfolio
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# OR for more specific control:
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Register blueprints
app.register_blueprint(contact_bp)
app.register_blueprint(chatbot_bp)

# Upload data on startup
with app.app_context():
    try:
        logger.info("Uploading portfolio data...")
        upload_portfolio()
    except Exception as e:
        logger.error(f"Failed to upload portfolio: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)