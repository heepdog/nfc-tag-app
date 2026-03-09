import sqlite3
import os
from datetime import datetime
import bcrypt


class Database:
    def __init__(self, db_path='nfc_app.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_approved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add is_approved column if it doesn't exist (migration for existing databases)
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_approved' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN is_approved INTEGER DEFAULT 0')
        
        # Create nfc_readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfc_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                infinity_sn TEXT NOT NULL,
                datetime TIMESTAMP NOT NULL,
                location_lat REAL,
                location_lng REAL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, password):
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None  # Username already exists
    
    def verify_user(self, username, password):
        """Verify user credentials and check approval status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, password_hash, is_approved FROM users WHERE username = ?',
            (username,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id, stored_hash, is_approved = result
            
            # Check if account is approved
            if not is_approved:
                return None  # Account not approved yet
            
            password_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, stored_hash):
                return user_id
        
        return None
    
    def get_pending_registrations(self):
        """Get all unapproved user registrations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, created_at
            FROM users
            WHERE is_approved = 0
            ORDER BY created_at ASC
        ''')
        
        registrations = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'username', 'created_at']
        return [dict(zip(columns, reg)) for reg in registrations]
    
    def approve_user(self, user_id):
        """Approve a pending user registration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def reject_user(self, user_id):
        """Reject and delete a pending user registration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = ? AND is_approved = 0', (user_id,))
        conn.commit()
        conn.close()
    
    def save_nfc_reading(self, infinity_sn, location_lat, location_lng, user_id):
        """Save NFC reading data to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO nfc_readings (infinity_sn, datetime, location_lat, location_lng, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (infinity_sn, datetime.now(), location_lat, location_lng, user_id))
        
        reading_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reading_id
    
    def get_user_readings(self, user_id, limit=50):
        """Get NFC readings for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, infinity_sn, datetime, location_lat, location_lng, created_at
            FROM nfc_readings
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        readings = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        columns = ['id', 'infinity_sn', 'datetime', 'location_lat', 'location_lng', 'created_at']
        return [dict(zip(columns, reading)) for reading in readings]
    
    def get_all_readings(self, limit=100):
        """Get all NFC readings with user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.infinity_sn, r.datetime, r.location_lat, r.location_lng, 
                   r.created_at, u.username
            FROM nfc_readings r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        readings = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'infinity_sn', 'datetime', 'location_lat', 'location_lng', 'created_at', 'username']
        return [dict(zip(columns, reading)) for reading in readings]


# Initialize database instance
db = Database()