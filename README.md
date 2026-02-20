# NFC Tag Reader Web Application

A web application that reads and writes NFC tags with InfinitySN field data, storing readings with timestamps, location, and user information.

## Features

- **NFC Reading**: Read InfinitySN data from NFC tags
- **NFC Writing**: Write InfinitySN data to NFC tags  
- **User Authentication**: Basic login system with user management
- **Location Tracking**: Capture GPS coordinates when reading tags
- **Data Storage**: SQLite database for readings and user data
- **Web Interface**: Responsive web UI with read/write modes

## Requirements

- Python 3.7+
- NFC-enabled Android device with Chrome browser
- HTTPS connection (required for Web NFC API)

## Installation

1. **Clone or download the project**
   ```bash
   cd nfc-tag-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   - Open Chrome on your Android device
   - Navigate to `https://your-server-ip:5000`
   - Accept the self-signed certificate warning

## Usage

### First Time Setup

1. When you first run the application, a default admin user will be created:
   - Username: `admin`
   - Password: `password123`
   - **Change this password immediately after first login!**

### Reading NFC Tags

1. Log in to the application
2. Ensure you're in "Read Mode" (default)
3. Allow location permissions when prompted
4. Tap "Scan NFC Tag"
5. Hold your device near an NFC tag containing InfinitySN data
6. The data will be automatically saved with timestamp and location

### Writing NFC Tags

1. Switch to "Write Mode"
2. Enter the InfinitySN value you want to write
3. Tap "Write to NFC Tag"
4. Hold your device near a writable NFC tag
5. The InfinitySN will be written in JSON format: `{"InfinitySN": "your-value"}`

### NFC Tag Format

The application expects/creates NFC tags with NDEF text records containing:
```json
{"InfinitySN": "your-serial-number"}
```

Alternative formats that will be recognized when reading:
- Plain text: `your-serial-number`
- Prefixed: `InfinitySN:your-serial-number`

## Production Deployment

### Using Gunicorn

1. **Install production dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export SECRET_KEY="your-secure-secret-key"
   export FLASK_ENV="production"
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn -c gunicorn.conf.py app:app
   ```

### HTTPS Setup

For production, you'll need proper SSL certificates. The Web NFC API requires HTTPS.

**Option 1: Reverse Proxy (Recommended)**
Use nginx or Apache as a reverse proxy with SSL termination.

**Option 2: Direct SSL**
Update `gunicorn.conf.py` to include your certificate files:
```python
keyfile = '/path/to/your/keyfile.pem'
certfile = '/path/to/your/certfile.pem'
```

## Database

The application uses SQLite with the following tables:

### users
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Bcrypt hashed password
- `created_at`: Registration timestamp

### nfc_readings
- `id`: Primary key
- `infinity_sn`: The InfinitySN value from the tag
- `datetime`: When the tag was read
- `location_lat`: GPS latitude (if available)
- `location_lng`: GPS longitude (if available)
- `user_id`: Foreign key to users table
- `created_at`: Database insertion timestamp

## API Endpoints

- `POST /api/login` - User authentication
- `POST /api/register` - User registration
- `POST /api/logout` - User logout
- `GET /api/user-info` - Get current user info
- `POST /api/nfc-data` - Save NFC reading
- `GET /api/nfc-data` - Get user's NFC readings

## Browser Support

The Web NFC API is currently only supported in:
- Chrome on Android (version 89+)
- Chrome OS (version 89+)

## Security Notes

1. Change the default admin password immediately
2. Use strong, unique passwords
3. In production, use proper SSL certificates
4. Consider implementing additional security measures like:
   - Rate limiting
   - CSRF protection
   - Input sanitization
   - User role management

## Troubleshooting

### NFC Not Working
- Ensure you're using Chrome on Android
- Check that NFC is enabled on your device
- Verify the connection is HTTPS
- Try refreshing the page and granting permissions again

### Location Not Working
- Allow location permissions in your browser
- Ensure location services are enabled on your device
- The app will work without location data if permissions are denied

### Database Issues
- The SQLite database file (`nfc_app.db`) will be created automatically
- Ensure the application has write permissions in its directory
- Database initialization happens automatically on first run

## Development

To run in development mode with debug logging:
```bash
export FLASK_ENV=development
python run.py
```

The application will reload automatically when code changes are detected.

## License

This project is provided as-is for demonstration purposes.