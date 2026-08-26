import sys
import os

# Ensure the root directory is on Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

# Expose WSGI handler for Vercel
handler = app
