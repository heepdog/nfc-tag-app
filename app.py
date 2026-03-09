from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_session import Session
import os
import secrets
from datetime import datetime, timedelta
from database import db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
from flask_wtf.csrf import CSRFProtect
import jwt
from functools import wraps
from flask import g

app = Flask(__name__)

csrf = CSRFProtect(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['ssl_context'] = os.environ.get('SSL_CONTEXT', 'adhoc')  # Use adhoc SSL for development by default
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JS cannot access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 min timeout

# Initialize Flask-Session
Session(app)

limiter = Limiter(app=app, 
                  key_func=get_remote_address, 
                  default_limits=["200 per day", "50 per hour"], 
                  storage_uri="memory://")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


def generate_jwt(user_id, hours=1):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=hours)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def verify_jwt(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except Exception:
        return None


def get_current_user_id():
    user_id = session.get('user_id')
    if user_id:
        return user_id
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(None, 1)[1]
        payload = verify_jwt(token)
        if payload:
            return payload.get('user_id')
    return None


def is_admin(user_id):
    """Check if user is admin (user_id = 1)"""
    return user_id == 1


def require_admin(f):
    """Decorator to require admin role for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id or not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        g.user_id = user_id
        return f(*args, **kwargs)
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
@csrf.exempt
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
        
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        user_id = db.create_user(username, password)
        
        if user_id:
            return jsonify({
                'success': True,
                'message': 'Registration successful. Your account is pending admin approval.',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'error': 'Username already exists'}), 409
    
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
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
            token = generate_jwt(user_id)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user_id': user_id,
                'token': token
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401  # For both cases
    
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/logout', methods=['POST'])
@csrf.exempt
def logout():
    """User logout endpoint"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/nfc-data', methods=['POST'])
@login_required
@csrf.exempt
def save_nfc_data():
    """Save NFC tag reading data"""
    try:
        data = request.get_json()
        infinity_sn = data.get('infinity_sn', '').strip()
        location_lat = data.get('location_lat')
        location_lng = data.get('location_lng')
        
        if not infinity_sn:
            return jsonify({'error': 'InfinitySN is required'}), 400
        
        if not (3 <= len(infinity_sn) <= 10):
            return jsonify({'error': 'InfinitySN must be between 3 and 10 characters'}), 400
        
        if not infinity_sn.isdigit():
            return jsonify({'error': 'InfinitySN must contain only numeric digits'}), 400
        
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
            user_id=g.user_id
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
        
        readings = db.get_user_readings(g.user_id, limit)
        
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
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    return jsonify({
        'user_id': user_id,
        'username': session.get('username')
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


@app.route("/api/admin/pending-registrations", methods=['GET'])
@require_admin
def get_pending_registrations():
    """Get all pending user registrations (admin only)"""
    try:
        registrations = db.get_pending_registrations()
        return jsonify({
            'success': True,
            'registrations': registrations,
            'count': len(registrations)
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve pending registrations'}), 500


@app.route("/api/admin/approve-user", methods=['POST'])
@require_admin
@csrf.exempt
def approve_user_registration():
    """Approve a pending user registration (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        db.approve_user(user_id)
        
        return jsonify({
            'success': True,
            'message': f'User {user_id} approved successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to approve user'}), 500


@app.route("/api/admin/reject-user", methods=['POST'])
@require_admin
@csrf.exempt
def reject_user_registration():
    """Reject and delete a pending user registration (admin only)"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        db.reject_user(user_id)
        
        return jsonify({
            'success': True,
            'message': f'User {user_id} rejected and deleted'
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to reject user'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

def validate_password(password):
    if len(password) < 6: #12:
        return False, "Password must be at least 12 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain number"
    # if not re.search(r"[!@#$%^&*]", password):
    #     return False, "Password must contain special character"
    return True, None


if __name__ == '__main__':
    # Run in development mode
    app.run(debug=True, host='0.0.0.0', port=5000) #, ssl_context='adhoc')