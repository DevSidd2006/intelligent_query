#!/usr/bin/env python3
"""
Simple Flask server runner
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    print("🚀 Starting Intelligent Query PDF Q&A System...")
    print("📍 Web Interface: http://localhost:3000")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        from src.web_app import app
        app.run(
            host='0.0.0.0',
            port=3000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()