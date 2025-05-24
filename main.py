from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.account import Account
from appwrite.id import ID
from appwrite.exception import AppwriteException
import os
from dotenv import load_dotenv
import logging
from functools import cache, wraps

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Protect routes that require authentication
def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

# Initialize Appwrite services
databases = Databases(client)
account = Account(client)

# Configure Flask session
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Get database configuration
database_id = os.getenv('DATABASE_ID')
collection_id = os.getenv('COLLECTION_ID')

@cache
def ensure_collection_attributes():
    """Ensure required attributes exist in the collection. This function is cached and will only run once."""
    try:
        # List attributes to check if they exist
        attributes = databases.list_attributes(
            database_id=database_id,
            collection_id=collection_id
        )
        
        # Get existing attribute keys
        existing_attrs = [attr['key'] for attr in attributes['attributes']]
        
        # Check and create content attribute if needed
        if 'content' not in existing_attrs:
            logger.info("Creating content attribute in collection...")
            databases.create_string_attribute(
                database_id=database_id,
                collection_id=collection_id,
                key='content',
                size=128,
                required=True
            )
            logger.info("Content attribute created successfully")
            
        logger.info("All required attributes are present in the collection.")
            
    except AppwriteException as e:
        logger.error(f"Error checking/creating attributes: {str(e)}")
        raise

@app.route('/')
@login_required
def index():
    """Render the main page with all todo items."""
    try:
        # With document security enabled, list_documents will automatically only return
        # documents the user has permission to access
        items = databases.list_documents(
            database_id=database_id,
            collection_id=collection_id
        )
        return render_template('index.html', items=items['documents'])
    except AppwriteException as e:
        logger.error(f"Failed to fetch documents: {str(e)}")
        return render_template('index.html', items=[], error=str(e))

@app.route('/items', methods=['POST'])
@login_required
def add_item():
    """Add a new todo item."""
    try:
        # Get content from JSON or form data
        content = request.json.get('content') if request.is_json else request.form.get('content')
        
        if not content:
            return "Content is required", 400

        # Create document in Appwrite
        # With document security enabled, the document will automatically be owned by the current user
        document_id = ID.unique()
        item = databases.create_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=document_id,
            data={
                'content': content
            },
            permissions=[
                f'read("user:{session["user_id"]}")',
                f'update("user:{session["user_id"]}")',
                f'delete("user:{session["user_id"]}")'
            ]
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
@login_required
def delete_item(item_id):
    """Delete a todo item."""
    try:
        # With document security enabled, delete_document will fail automatically
        # if the user doesn't have permission to delete the document
        databases.delete_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=item_id
        )
        return '', 200
    except AppwriteException as e:
        logger.error(f"Failed to delete document {item_id}: {str(e)}")
        return str(e), 500

@app.route('/items/<item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    """Update a todo item."""
    try:
        # Get content from JSON or form data
        content = request.json.get('content') if request.is_json else request.form.get('content')
        
        if not content:
            return "Content is required", 400

        # Update document in Appwrite
        # Document security will automatically check if user has permission
        item = databases.update_document(
            database_id=database_id,
            collection_id=collection_id,
            document_id=item_id,
            data={
                'content': content
            }
        )

        # Transform item for template
        item_view = {
            '$id': item['$id'],
            'content': content
        }
        
        return render_template('partials/item.html', item=item_view)
    except AppwriteException as e:
        logger.error(f"Failed to update document {item_id}: {str(e)}")
        return str(e), 500

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')

            # Create user account
            user = account.create(
                user_id=ID.unique(),
                email=email,
                password=password,
                name=name
            )

            # Create session for the new user
            session_data = account.create_email_password_session(email, password)
            session['user_id'] = user['$id']
            session['user_name'] = name
            
            return redirect(url_for('index'))
        except AppwriteException as e:
            logger.error(f"Registration failed: {str(e)}")
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            # Create session
            session_data = account.create_email_password_session(email, password)
            session['user_id'] = session_data['userId']
            
            # Get user data and store name in session
            user = account.get()
            session['user_name'] = user['name']
            
            return redirect(url_for('index'))
        except AppwriteException as e:
            logger.error(f"Login failed: {str(e)}")
            return render_template('login.html', error=str(e))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    try:
        if 'user_id' in session:
            # Delete the current session
            account.delete_session('current')
            session.clear()  # Clear all session data
    except AppwriteException as e:
        logger.error(f"Logout failed: {str(e)}")
    
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Check if required environment variables are set
    required_vars = ['APPWRITE_PROJECT_ID', 'APPWRITE_API_KEY', 'DATABASE_ID', 'COLLECTION_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
        
    # Ensure required attributes exist
    ensure_collection_attributes()

    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 