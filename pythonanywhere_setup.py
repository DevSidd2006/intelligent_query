#!/usr/bin/env python3
"""
PythonAnywhere Setup Script
Run this script in your PythonAnywhere console to set up the environment
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def setup_pythonanywhere():
    """Setup the application for PythonAnywhere"""
    
    print("🚀 Setting up Intelligent Query for PythonAnywhere...")
    
    # Create necessary directories
    directories = ['logs', 'uploads', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Install requirements
    if not run_command("pip3.10 install --user -r requirements.txt", "Installing Python packages"):
        print("⚠️ Some packages may have failed to install. Check the output above.")
    
    # Set up environment variables
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"\n📝 Creating {env_file} file...")
        with open(env_file, 'w') as f:
            f.write("""# PythonAnywhere Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-change-this
OPENROUTER_API_KEY=your-openrouter-api-key-here
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
""")
        print(f"✅ Created {env_file} - Please update with your actual API keys!")
    
    # Create a simple test script
    with open('test_setup.py', 'w') as f:
        f.write("""#!/usr/bin/env python3
import sys
import os

print("Testing PythonAnywhere setup...")

# Test imports
try:
    import flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    import sentence_transformers
    print("✅ Sentence Transformers imported successfully")
except ImportError as e:
    print(f"❌ Sentence Transformers import failed: {e}")

try:
    import faiss
    print("✅ FAISS imported successfully")
except ImportError as e:
    print(f"❌ FAISS import failed: {e}")

# Test app import
try:
    sys.path.insert(0, 'src')
    from web_app import app
    print("✅ Web app imported successfully")
except ImportError as e:
    print(f"❌ Web app import failed: {e}")

print("Setup test completed!")
""")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Update the .env file with your actual API keys")
    print("2. Update wsgi.py with your actual PythonAnywhere username and path")
    print("3. Run 'python3.10 test_setup.py' to test the setup")
    print("4. Configure your web app in PythonAnywhere dashboard")
    print("5. Set the source code path to: /home/yourusername/intelligent_query")
    print("6. Set the WSGI configuration file to: /home/yourusername/intelligent_query/wsgi.py")

if __name__ == "__main__":
    setup_pythonanywhere()