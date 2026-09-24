import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.views.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.views.incidents import incidents as incidents_blueprint
    app.register_blueprint(incidents_blueprint)

    from app.views.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from app.views.dashboard import dashboard as dashboard_blueprint
    app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')

    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        from app.utils.constants import ROLE_REPORTER
        
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        if current_user.role == ROLE_REPORTER:
            return redirect(url_for('incidents.list_incidents'))
        return redirect(url_for('dashboard.index'))

    return app
