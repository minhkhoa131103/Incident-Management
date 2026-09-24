from datetime import datetime
from app import db
from app.utils.constants import STATUS_OPEN, PRIORITY_LOW

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default=PRIORITY_LOW)
    status = db.Column(db.String(20), nullable=False, default=STATUS_OPEN)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = db.relationship('Comment', backref='incident', lazy='dynamic', cascade='all, delete-orphan')
