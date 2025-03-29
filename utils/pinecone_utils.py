import os
import google.generativeai as genai
from pinecone import Pinecone  # Updated import
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pinecone (new syntax)
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("portfolio-index")  # Updated initialization

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def create_embedding(text):
    try:
        result = genai.embed_content(
            model='models/embedding-001',
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"EMBEDDING ERROR: {str(e)}")
        return None