from flask import Blueprint, request, jsonify
from utils.email_utils import send_email
from datetime import datetime
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

contact_bp = Blueprint('contact', __name__)

# MongoDB Configuration with error handling
try:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable not set")
    
    client = MongoClient(
        mongo_uri,
        connectTimeoutMS=5000,  # 5 seconds connection timeout
        socketTimeoutMS=30000,  # 30 seconds socket timeout
        serverSelectionTimeoutMS=5000  # 5 seconds server selection timeout
    )
    
    # Test the connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
    
    db = client.form
    contacts = db["form-data"]
    
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    # In production, you might want to fail fast here
    raise

@contact_bp.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['name', 'email', 'message']
        if not all(key in data for key in required_fields):
            missing = [field for field in required_fields if field not in data]
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing)}'
            }), 400

        # Create contact document
        contact = {
            'name': data['name'],
            'email': data['email'],
            'subject': data.get('subject', 'No Subject'),
            'message': data['message'],
            'created_at': datetime.utcnow(),
            'ip_address': request.remote_addr,
            'status': 'new'
        }

        # Insert into MongoDB
        result = contacts.insert_one(contact)
        if not result.inserted_id:
            raise Exception("Failed to insert contact into database")

        # Send confirmation email to user
        send_email(
            data['email'],
            "Thanks for contacting us!",
            "We will get back to you soon."
        )

        # Send notification to admin
        admin_email = os.getenv("ADMIN_EMAIL")
        if admin_email:
            send_email(
                admin_email,
                "New Contact Form Submission",
                f"""
                New contact form submission:
                Name: {data['name']}
                Email: {data['email']}
                Subject: {data.get('subject', 'No Subject')}
                Message: {data['message']}
                """
            )

        return jsonify({
            'success': True,
            'message': 'Form submitted successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500