import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Configure for production
app.config.update({
    'ENV': 'production',
    'DEBUG': False,
})

# Export the app for Vercel
app = app