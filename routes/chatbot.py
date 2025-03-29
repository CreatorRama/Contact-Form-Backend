from flask import Blueprint, request, jsonify
from utils.pinecone_utils import create_embedding, index
import google.generativeai as genai
import time
import logging
import json

chatbot_bp = Blueprint('chatbot', __name__)
logger = logging.getLogger(__name__)

# Load resume data
with open('resume.json') as f:
    RESUME_DATA = json.load(f)

# Configuration
generation_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 512,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

model = genai.GenerativeModel(
    'models/gemini-1.5-flash-latest',
    generation_config=generation_config,
    safety_settings=safety_settings
)

def get_contact_info():
    """Extract contact information from resume data"""
    contact = RESUME_DATA.get('contact', {})
    return (
        f"Contact Information:\n"
        f"Email: {contact.get('email', 'Not available')}\n"
        f"Phone: {contact.get('phone', 'Not available')}\n"
        f"Portfolio: {contact.get('portfolio', 'Not available')}\n"
        f"GitHub: {contact.get('github', 'Not available')}\n"
        f"LinkedIn: {contact.get('linkedin', 'Not available')}\n"
        f"LeetCode: {contact.get('leetcode', 'Not available')}\n"
        f"Address: {contact.get('address', 'Not available')}"
    )

@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').lower().strip()
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
            
        # Handle contact information request directly
        if any(keyword in message for keyword in ['contact', 'email', 'phone', 'linkedin', 'github', 'portfolio']):
            contact_info = get_contact_info()
            return jsonify({
                'reply': contact_info,
                'sources': [{
                    'type': 'contact',
                    'category': 'personal',
                    'text': 'Contact information from resume'
                }]
            })
            
        time.sleep(1)  # Rate limiting
        
        query_embedding = create_embedding(message)
        if not query_embedding:
            return jsonify({'error': 'Failed to process message'}), 500
            
        response = index.query(
            vector=query_embedding,
            top_k=3,  # Increased to get more context
            include_metadata=True
        )
        
        context = "\n".join(
            match['metadata']['text']
            for match in response['matches']
            if match.get('metadata', {}).get('text')
        ) or "No context available"
        
        prompt = f"""You are a professional portfolio assistant. Answer based on this context:
{context}

If the question is about contact information, skills, projects, education, or certifications, 
provide specific details from the resume data.

Question: {message}"""
        
        result = model.generate_content(prompt)
        
        # Post-process the response to ensure accuracy
        reply = result.text
        if "contact information" in message.lower() and "contact information" not in reply.lower():
            reply = get_contact_info() + "\n\n" + reply
            
        return jsonify({
            'reply': reply,
            'sources': [match['metadata'] for match in response['matches'] if match.get('metadata')]
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({
            'reply': "I'm having trouble responding. Please try again later.",
            'error': str(e)
        }), 500