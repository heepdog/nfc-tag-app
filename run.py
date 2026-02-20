#!/usr/bin/env python3.11
"""
Production runner for NFC Tag Reader application
"""
import os
import sys
from app import app

def create_default_user():
    """Create a default admin user if no users exist"""
    from database import db
    
    # Check if any users exist
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    conn.close()
    
    # Create default admin user if none exist
    if user_count == 0:
        print("No users found. Creating default admin user...")
        user_id = db.create_user('admin', 'password123')
        if user_id:
            print("Default admin user created:")
            print("  Username: admin")
            print("  Password: password123")
            print("  Please change this password after first login!")
        else:
            print("Failed to create default admin user")

if __name__ == '__main__':
    # Ensure database is initialized and create default user
    create_default_user()
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    if len(sys.argv) > 1 and sys.argv[1] == '--production':
        print("Starting in production mode...")
        print("Use gunicorn for production deployment:")
        print("  gunicorn -c gunicorn.conf.py app:app")
        # return
    
    # SSL Configuration
    ssl_context = None
    use_ssl = '--no-ssl' not in sys.argv
    
    if use_ssl:
        try:
            # Try to use adhoc SSL (requires cryptography library)
            # ssl_context = 'adhoc'
            ssl_context = ('cert.pem', 'key.pem')  # Use custom certs if available
            print("Starting in development mode with HTTPS...")
        except Exception as e:
            print(f"Warning: Could not enable HTTPS: {e}")
            print("Starting in development mode with HTTP...")
            print("Note: NFC functionality requires HTTPS. Install cryptography library or use a reverse proxy.")
            ssl_context = None
    else:
        print("Starting in development mode with HTTP (SSL disabled)...")
        print("Note: NFC functionality requires HTTPS.")
    
    print(f"Server will be available at: {'https' if ssl_context else 'http'}://{host}:{port}")
    print("For production, use: python run.py --production")
    print("To disable SSL, use: python run.py --no-ssl")
    print()
    
    try:
        app.run(debug=debug, host=host, port=port, ssl_context=ssl_context)
    except Exception as e:
        if 'cryptography' in str(e).lower():
            print("\nError: SSL requires the cryptography library.")
            print("Options to fix this:")
            print("1. Install cryptography: pip install cryptography")
            print("2. Run without SSL: python run.py --no-ssl")
            print("3. Use a reverse proxy (nginx) for HTTPS")
        else:
            print(f"\nError starting server: {e}")
        sys.exit(1)
