from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_session import Session
import os
import secrets
from datetime import datetime
from database import db

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Initialize Flask-Session
Session(app)


def login_required(f):
    """Decorator to require login for protected routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@app.route('/')
def index():
    """Main application page"""
    if 'user_id' in session:
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')


@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        user_id = db.create_user(username, password)
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'error': 'Username already exists'}), 409
    
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user_id = db.verify_user(username, password)
        
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user_id': user_id
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/nfc-data', methods=['POST'])
@login_required
def save_nfc_data():
    """Save NFC tag reading data"""
    try:
        data = request.get_json()
        infinity_sn = data.get('infinity_sn', '').strip()
        location_lat = data.get('location_lat')
        location_lng = data.get('location_lng')
        
        if not infinity_sn:
            return jsonify({'error': 'InfinitySN is required'}), 400
        
        # Validate location data if provided
        if location_lat is not None:
            try:
                location_lat = float(location_lat)
                if not (-90 <= location_lat <= 90):
                    return jsonify({'error': 'Invalid latitude'}), 400
            except (ValueError, TypeError):
                location_lat = None
        
        if location_lng is not None:
            try:
                location_lng = float(location_lng)
                if not (-180 <= location_lng <= 180):
                    return jsonify({'error': 'Invalid longitude'}), 400
            except (ValueError, TypeError):
                location_lng = None
        
        reading_id = db.save_nfc_reading(
            infinity_sn=infinity_sn,
            location_lat=location_lat,
            location_lng=location_lng,
            user_id=session['user_id']
        )
        
        return jsonify({
            'success': True,
            'message': 'NFC data saved successfully',
            'reading_id': reading_id
        }), 201
    
    except Exception as e:
        return jsonify({'error': 'Failed to save NFC data'}), 500


@app.route('/api/nfc-data', methods=['GET'])
@login_required
def get_nfc_data():
    """Get NFC readings for the current user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # Cap at 200 records
        
        readings = db.get_user_readings(session['user_id'], limit)
        
        return jsonify({
            'success': True,
            'readings': readings,
            'count': len(readings)
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve NFC data'}), 500


@app.route('/api/user-info', methods=['GET'])
@login_required
def get_user_info():
    """Get current user information"""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username']
    }), 200

@app.route("/api/all-readings", methods=['GET'])
@login_required
def get_all_readings():
    """Get all NFC readings (admin only)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)  # Cap at 200 records
        
        readings = db.get_all_readings(limit)
        
        return jsonify({
            'success': True,
            'readings': readings,
            'count': len(readings)
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve all NFC data'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Run in development mode
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc')