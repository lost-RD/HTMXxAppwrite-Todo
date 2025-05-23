from flask import Flask, render_template, request, jsonify
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.exception import AppwriteException
import os
from dotenv import load_dotenv
import logging
from functools import cache

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Appwrite client
client = Client()
client.set_endpoint(os.getenv('APPWRITE_ENDPOINT', 'https://cloud.appwrite.io/v1'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
client.set_key(os.getenv('APPWRITE_API_KEY'))

# Get database configuration
database_id = os.getenv('DATABASE_ID')
collection_id = os.getenv('COLLECTION_ID')

# Initialize Appwrite Databases service
databases = Databases(client)

@cache
def ensure_content_attribute():
    """Ensure the content attribute exists in the collection. This function is cached and will only run once."""
    try:
        # List attributes to check if content exists
        attributes = databases.list_attributes(
            database_id=database_id,
            collection_id=collection_id
        )
        
        # Check if content attribute exists
        has_content_attr = any(attr['key'] == 'content' for attr in attributes['attributes'])
        
        if not has_content_attr:
            logger.info("Creating content attribute in collection...")
            databases.create_string_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key='content',
                size=128,
                required=True
            )
            logger.info("Content attribute created successfully")
            
    except AppwriteException as e:
        logger.error(f"Error checking/creating content attribute: {str(e)}")
        raise

@app.route('/')
def index():
    """Render the main page with all todo items."""
    try:
        items = databases.list_documents(
            database_id=database_id,
            collection_id=collection_id
        )
        return render_template('index.html', items=items['documents'])
    except AppwriteException as e:
        logger.error(f"Failed to fetch documents: {str(e)}")
        return render_template('index.html', items=[], error=str(e))

@app.route('/items', methods=['POST'])
def add_item():
    """Add a new todo item."""
    try:
        # Ensure content attribute exists
        ensure_content_attribute()
        
        # Get content from JSON or form data
        content = request.json.get('content') if request.is_json else request.form.get('content')
        
        if not content:
            return "Content is required", 400

        # Create document in Appwrite
        document_id = ID.unique()
        item = databases.create_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=document_id,
            data={'content': content}
        )

        # Transform item for template
        item_view = {
            '$id': item['$id'],
            'content': content
        }
        
        return render_template('partials/item.html', item=item_view)
    except AppwriteException as e:
        logger.error(f"Failed to create document: {str(e)}")
        return str(e), 500

@app.route('/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete a todo item."""
    try:
        databases.delete_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=item_id
        )
        return '', 200
    except AppwriteException as e:
        logger.error(f"Failed to delete document {item_id}: {str(e)}")
        return str(e), 500

if __name__ == '__main__':
    # Check if required environment variables are set
    required_vars = ['APPWRITE_PROJECT_ID', 'APPWRITE_API_KEY', 'DATABASE_ID', 'COLLECTION_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
        
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 