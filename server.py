from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
import smtplib
import ssl
from email.message import EmailMessage
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

# Gmail SMTP configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_SENDER = os.getenv("EMAIL_SENDER")  # Your Gmail address
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App password
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")  # Your email for notifications

def send_email(to_email, subject, body):
    """Function to send email via Gmail SMTP."""
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

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
            'status': 'new'
        }
        
        # Insert into MongoDB
        result = contacts.insert_one(contact)

        # Send confirmation email to the sender
        sender_subject = "Thank you for reaching out!"
        sender_body = f"""
        Hello {data['name']},

        Thank you for your message:
        "{data['message']}"

        We will get back to you soon!

        Best Regards,
        Your Team
        """
        send_email(data['email'], sender_subject, sender_body)

        # Send notification email to admin
        admin_subject = "New Contact Form Submission"
        admin_body = f"""
        New contact form submitted:

        Name: {data['name']}
        Email: {data['email']}
        Subject: {data.get('subject', 'No subject')}
        Message: {data['message']}
        IP Address: {request.remote_addr}

        Please follow up with them.
        """
        send_email(ADMIN_EMAIL, admin_subject, admin_body)

        return jsonify({
            'success': True,
            'message': 'Contact form submitted successfully. Emails sent!',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'API is running'
    })

if __name__ == '__main__':
    app.run(debug=True)
