# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = 'nfc_tag_app'

# Server mechanics
daemon = False
pidfile = '/tmp/nfc_tag_app.pid'
user = None
group = None
tmp_upload_dir = None

# SSL/HTTPS Configuration (for production with proper certificates)
# keyfile = '/path/to/keyfile.pem'
# certfile = '/path/to/certfile.pem'

# Development SSL (self-signed certificate)
# Only use this for development - use proper certificates in production
ssl_version = None  # Disable SSL in gunicorn, use reverse proxy (nginx) for HTTPS

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190