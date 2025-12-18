#!/usr/bin/env python3
"""
WSGI configuration for PythonAnywhere deployment
This file is used by PythonAnywhere to serve your Flask application
"""

import sys
import os

# Add your project directory to Python path
project_home = '/home/yourusername/intelligent_query'  # Update this path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add the src directory to Python path
src_path = os.path.join(project_home, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import your Flask application
from src.web_app import app as application

if __name__ == "__main__":
    application.run()