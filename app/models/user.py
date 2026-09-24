from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from app.utils.constants import ROLE_REPORTER

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # NEW fields
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    role_rel = db.relationship('Role', backref='users')
    incidents_reported = db.relationship('Incident', foreign_keys='Incident.reporter_id', backref='reporter', lazy='dynamic')
    incidents_assigned = db.relationship('Incident', foreign_keys='Incident.assignee_id', backref='assignee', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    @property
    def role(self):
        return self.role_rel.name if self.role_rel else None

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm_name):
        if not self.role_rel:
            return False
        return self.role_rel.has_permission(perm_name)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
