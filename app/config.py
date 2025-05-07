import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'secret-key-goes-here'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=120)
    
    # File upload configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'Uploads')
    ALLOWED_EXTENSIONS = {'md', 'xml', 'csv', 'png', 'jpg', 'jpeg'}