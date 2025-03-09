from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.form  # database name
contacts = db["form-data"]  # collection name

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        # Get form data from request
        data = request.json
        
        # Validate required fields
        if not all(key in data for key in ['name', 'email', 'message']):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
            
        # Create contact document
        contact = {
            'name': data['name'],
            'email': data['email'],
            'subject': data.get('subject', ''),  # Optional field
            'message': data['message'],
            'created_at': datetime.utcnow(),
            'ip_address': request.remote_addr,
            'status': 'new'  # You can use this to track if you've responded
        }
        
        # Insert into MongoDB
        result = contacts.insert_one(contact)
        
        return jsonify({
            'success': True,
            'message': 'Contact form submitted successfully',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        # Log the error (in a production app, use a proper logging system)
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500

# Simple endpoint to test if the API is running
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'API is running'
    })

if __name__ == '__main__':
    app.run(debug=True)