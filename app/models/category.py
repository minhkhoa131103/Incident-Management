from app import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Relationships
    incidents = db.relationship('Incident', backref='category', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Category, self).__init__(**kwargs)
