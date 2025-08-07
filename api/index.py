import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable for Vercel before importing the app
os.environ['VERCEL'] = '1'

# Import the main Flask application (it will handle Vercel setup internally)
from app import app