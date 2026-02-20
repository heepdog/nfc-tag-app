#!/usr/bin/env python3
"""
Test script to verify the NFC Tag Reader application setup
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing module imports...")
    
    try:
        import sqlite3
        print("✓ sqlite3 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import sqlite3: {e}")
        return False
    
    try:
        import flask
        print(f"✓ Flask {flask.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import flask: {e}")
        return False
    
    try:
        import bcrypt
        print(f"✓ bcrypt imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import bcrypt: {e}")
        return False
    
    try:
        from flask_session import Session
        print("✓ Flask-Session imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import flask_session: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\nTesting database functionality...")
    
    try:
        from database import Database
        print("✓ Database module imported successfully")
        
        # Create test database
        test_db = Database('test_nfc.db')
        print("✓ Test database created successfully")
        
        # Test user creation
        user_id = test_db.create_user('testuser', 'testpass123')
        if user_id:
            print("✓ Test user created successfully")
        else:
            print("✗ Failed to create test user")
            return False
        
        # Test user verification
        verified_id = test_db.verify_user('testuser', 'testpass123')
        if verified_id == user_id:
            print("✓ User verification works")
        else:
            print("✗ User verification failed")
            return False
        
        # Test NFC reading storage
        reading_id = test_db.save_nfc_reading('TEST123', 37.7749, -122.4194, user_id)
        if reading_id:
            print("✓ NFC reading storage works")
        else:
            print("✗ Failed to store NFC reading")
            return False
        
        # Test reading retrieval
        readings = test_db.get_user_readings(user_id)
        if readings and len(readings) == 1:
            print("✓ Reading retrieval works")
            print(f"  Retrieved: {readings[0]['infinity_sn']}")
        else:
            print("✗ Failed to retrieve readings")
            return False
        
        # Cleanup
        os.remove('test_nfc.db')
        print("✓ Test database cleaned up")
        
        return True
    
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_flask_app():
    """Test Flask app creation"""
    print("\nTesting Flask application...")
    
    try:
        from app import app
        print("✓ Flask app imported successfully")
        
        # Test app configuration
        if app.config.get('SECRET_KEY'):
            print("✓ App has secret key configured")
        else:
            print("✗ App missing secret key")
            return False
        
        # Test that we can create app context
        with app.app_context():
            print("✓ App context created successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Flask app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("NFC Tag Reader Application Setup Test")
    print("="*40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test database
    if not test_database():
        success = False
    
    # Test Flask app
    if not test_flask_app():
        success = False
    
    print("\n" + "="*40)
    if success:
        print("✓ All tests passed! Application is ready to run.")
        print("\nTo start the application:")
        print("  python run.py")
        print("\nFor production:")
        print("  gunicorn -c gunicorn.conf.py app:app")
    else:
        print("✗ Some tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())