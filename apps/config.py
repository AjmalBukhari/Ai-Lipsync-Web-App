import os
import random
import string


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Set up the App SECRET_KEY
    SECRET_KEY = os.getenv('cyber', None)
    if not SECRET_KEY:
        SECRET_KEY = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # # PostgreSQL Configuration
    # DB_ENGINE = os.getenv('DB_ENGINE', 'postgresql')
    # DB_USERNAME = os.getenv('DB_USERNAME', 'postgres')
    # DB_PASS = os.getenv('DB_PASS', 'virus')
    # DB_HOST = os.getenv('DB_HOST', 'localhost')
    # DB_PORT = os.getenv('DB_PORT', '5432')
    # DB_NAME = os.getenv('DB_NAME', 'postgres')

    DB_ENGINE = 'postgresql'
    DB_USERNAME = 'postgres'
    DB_PASS = 'virus'
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_NAME = 'postgres'

    SQLALCHEMY_DATABASE_URI = f'{DB_ENGINE}://{DB_USERNAME}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print("Database URL:", SQLALCHEMY_DATABASE_URI)

    # Assets Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')


    SOCIAL_AUTH_GITHUB = False

    GITHUB_ID = os.getenv('GITHUB_ID')
    GITHUB_SECRET = os.getenv('GITHUB_SECRET')

    # Enable/Disable Github Social Login    
    if GITHUB_ID and GITHUB_SECRET:
        SOCIAL_AUTH_GITHUB = True

    # Profile Image Upload Settings
    USER_DATA_ROOT = os.path.join(basedir, 'user_data')
    PROFILE_IMAGE_NAME = 'profile_image.jpg'
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # User upload folders settings
    UPLOAD_FOLDER = 'apps/user_data/'
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac'}

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600



class ProductionConfig(Config):
    DEBUG = True
    # Additional production-specific settings if needed


class DebugConfig(Config):
    DEBUG = True


# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
