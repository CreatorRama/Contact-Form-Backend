import json
from utils.pinecone_utils import create_embedding, index

# Load resume data
with open('resume.json', 'r') as file:
    resume = json.load(file)

# Function to flatten and structure resume data
def flatten_resume(resume):
    data = []
    id = 0

    # Flatten projects
    if 'projects' in resume:
        for project in resume['projects']:
            data.append({
                'id': str(id),
                'text': f"{project['name']}: {project['description']}",
                'metadata': {
                    'type': 'project', 
                    'name': project['name'],
                    'text': f"Project: {project['name']}\nDescription: {project['description']}"  # Added for better context
                }
            })
            id += 1

    # Flatten skills
    if 'skills' in resume:
        for category, skills in resume['skills'].items():
            data.append({
                'id': str(id),
                'text': f"Skills in {category}: {', '.join(skills)}",
                'metadata': {
                    'type': 'skill', 
                    'category': category,
                    'text': f"Skills in {category}: {', '.join(skills)}"  # Added for better context
                }
            })
            id += 1

    # Flatten education
    if 'education' in resume:
        data.append({
            'id': str(id),
            'text': f"Education: {resume['education']['degree']} at {resume['education']['institution']}",
            'metadata': {
                'type': 'education',
                'text': f"Education: {resume['education']['degree']} at {resume['education']['institution']}"
            }
        })
        id += 1

    # Flatten summary
    if 'summary' in resume:
        data.append({
            'id': str(id),
            'text': resume['summary'],
            'metadata': {
                'type': 'summary',
                'text': resume['summary']
            }
        })

    return data

# Function to upload resume data to Pinecone
def upload_portfolio():
    flattened_data = flatten_resume(resume)
    vectors = []

    for item in flattened_data:
        embedding = create_embedding(item['text'])
        vectors.append({
            'id': item['id'],
            'values': embedding,
            'metadata': item['metadata']
        })

    index.upsert(vectors)
    print('Portfolio data uploaded!')