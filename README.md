# HTMX + Appwrite Todo App

A modern, real-time todo application built with HTMX and Appwrite. This demo showcases how to build a fast, lightweight web application with minimal JavaScript using HTMX for dynamic interactions and Appwrite as a backend service.

## Features

- ⚡ Real-time updates using HTMX
- 🔒 Secure backend with Appwrite
- 🎨 Modern UI with Tailwind CSS
- 🚀 Fast and lightweight - no JavaScript required!
- 🐳 Docker support for easy deployment
- 📱 Responsive design for mobile and desktop
- 🔐 Document-level security with user ownership
- ✏️ Inline editing with optimistic UI
- 🎯 Intuitive hover interactions on desktop

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.10 or higher
- An Appwrite account and project
- Docker and Docker Compose (optional)
- pip (Python package manager)

## Appwrite Setup

1. Create a new project in [Appwrite Console](https://cloud.appwrite.io)
2. Create a new database
3. Create a collection with the following schema:
   ```
   content (string, required)
   ```
4. Enable Document Security in the collection settings
5. Create an API key with the following permissions:
   - databases.collections.read
   - databases.documents.read
   - databases.documents.write
   - databases.documents.delete
   - users.read
   - users.write

6. Note down the following values:
   - Project ID
   - API Key
   - Database ID
   - Collection ID

## Security Model

The application implements a robust security model:

- User Authentication:
  - Secure registration and login system
  - Session-based authentication
  - Automatic session cleanup on logout

- Document Security:
  - Each todo item is owned by its creator
  - Users can only see their own items
  - Document-level permissions using Appwrite's security rules
  - Automatic permission validation on all operations

## User Interface

The application features a responsive design that works well on both mobile and desktop:

- Desktop:
  - Clean, minimal interface
  - Action buttons appear on hover
  - Smooth transitions and animations
  - Intuitive edit and delete controls

- Mobile:
  - Touch-friendly interface
  - Always-visible action buttons
  - Compact header design
  - Optimized spacing and typography

## Quick Start

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/htmx-appwrite-todo.git
   cd htmx-appwrite-todo
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` with your Appwrite credentials

4. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```

5. Open http://localhost:5000 in your browser

### Manual Setup

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/yourusername/htmx-appwrite-todo.git
   cd htmx-appwrite-todo
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy and configure the environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Appwrite credentials
   ```

5. Start the server:
   ```bash
   python main.py
   ```

6. Open http://localhost:5000 in your browser

## Project Structure

```
.
├── Dockerfile           # Docker configuration
├── compose.yml         # Docker Compose configuration
├── main.py            # Flask application
├── requirements.txt   # Python dependencies
├── templates/          
│   ├── index.html    # Main template with HTMX
│   └── partials/       
│       └── item.html # Todo item template
├── .env.example      # Example environment variables
└── .env              # Your environment variables (create this)
```

## Development

### Environment Variables

- `APPWRITE_ENDPOINT`: Appwrite API endpoint (default: https://cloud.appwrite.io/v1)
- `APPWRITE_PROJECT_ID`: Your Appwrite project ID
- `APPWRITE_API_KEY`: Your Appwrite API key
- `DATABASE_ID`: Your Appwrite database ID
- `COLLECTION_ID`: Your Appwrite collection ID
- `FLASK_DEBUG`: Enable debug mode (true/false)

### Docker Commands

```bash
# Build and start
docker compose up --build

# Start (after building)
docker compose up

# Stop
docker compose down

# View logs
docker compose logs -f
```

## Technologies Used

- [HTMX](https://htmx.org/) - High power tools for HTML
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Appwrite](https://appwrite.io/) - Backend as a Service
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Docker](https://www.docker.com/) - Container platform

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 