import os
import sys

# Set environment variables FIRST, before any imports
os.environ['VERCEL'] = '1'
os.environ['DEPLOYED'] = 'true'

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main Flask application (it will handle Vercel setup internally)
from app import app