import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')  # Fallback
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cookie Security Settings
    # HttpOnly is True by default in Flask for session cookies
    # SESSION_COOKIE_SECURE should be True in production (HTTPS), False in dev
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = Config.SECRET_KEY or 'dev-fallback-secret-do-not-use-in-production'

class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = Config.SECRET_KEY or 'testing-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    WTF_CSRF_CHECK_DEFAULT = False

class ProductionConfig(Config):
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
