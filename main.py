from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response, g
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Flask session
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Get database configuration
database_id = os.getenv('DATABASE_ID')
collection_id = os.getenv('COLLECTION_ID')

# Protect routes that require authentication
def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
            
        # Get session secret from cookie
        session_secret = request.cookies.get('appwrite_session')
        if not session_secret:
            session.clear()
            return redirect(url_for('login'))
            
        # Set session for client
        client = get_client()
        client.set_session(session_secret)
        
        # Store client in g object for route to use
        g.client = client
        return f(*args, **kwargs)
    return decorated_function

def get_client():
    client = Client()
    client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
    client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
    return client

def get_user_client():
    client = get_client()
    session_secret = request.cookies.get('appwrite_session')
    if session_secret:
        client.set_session(session_secret)
    return client

def get_admin_client():
    client = get_client()
    client.set_key(os.getenv('APPWRITE_API_KEY'))
    return client

@cache
def ensure_collection_attributes():
    """Ensure required attributes exist in the collection. This function is cached and will only run once."""
    try:
        databases = Databases(get_admin_client())

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
        # Use the authenticated client from the decorator
        databases = Databases(g.client)
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

        # Create document in Appwrite using admin client to bypass permissions
        document_id = ID.unique()
        databases = Databases(get_admin_client())
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
        databases = Databases(get_user_client())
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
        databases = Databases(get_user_client())
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
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        # Create user account
        account = Account(get_client())
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
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Create session using admin client
        account = Account(get_admin_client())
        session_data = account.create_email_password_session(email, password)
        
        # Create response with redirect
        response = make_response(redirect(url_for('index')))
        
        # Set secure cookie with session secret
        response.set_cookie(
            'appwrite_session',
            session_data['secret'],
            httponly=True,
            secure=True,
            samesite='Lax',
            expires=session_data['expire']
        )
        
        # Create new client with session and get account details
        client = get_client()
        client.set_session(session_data['secret'])
        account = Account(client)
        account_data = account.get()
        
        # Store user info in Flask session
        session['user_id'] = session_data['userId']
        session['user_name'] = account_data['name']
        
        return response
    
    return render_template('login.html')

@app.route('/guest-login')
def guest_login():
    """Handle guest login by creating an anonymous session."""
    try:
        # Create anonymous session using admin client
        account = Account(get_admin_client())
        session_data = account.create_anonymous_session()
        
        # Create response with redirect
        response = make_response(redirect(url_for('index')))
        
        # Set secure cookie with session secret
        response.set_cookie(
            'appwrite_session',
            session_data['secret'],
            httponly=True,
            secure=True,
            samesite='Lax',
            expires=session_data['expire']
        )
        
        # Store user info in Flask session
        session['user_id'] = session_data['userId']
        session['user_name'] = 'Guest'
        
        return response
    except AppwriteException as e:
        logger.error(f"Failed to create guest session: {str(e)}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Handle user logout."""
    try:
        if 'user_id' in session:
            # Get the session secret from cookie
            session_secret = request.cookies.get('appwrite_session')
            if session_secret:
                # Create client with session
                client = get_client()
                client.set_session(session_secret)
                account = Account(client)
                
                # Delete the current session
                account.delete_session('current')
                
                # Create response and clear cookies
                response = make_response(redirect(url_for('login')))
                response.delete_cookie('appwrite_session')
                session.clear()
                return response
    except AppwriteException as e:
        logger.error(f"Error during logout: {str(e)}")
    
    # If anything fails, still clear local session and redirect
    session.clear()
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