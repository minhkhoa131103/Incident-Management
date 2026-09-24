from app import db

# Association table
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __init__(self, **kwargs):
        super(Permission, self).__init__(**kwargs)

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_system = db.Column(db.Boolean, default=False, nullable=False)

    permissions = db.relationship('Permission', secondary=role_permissions, lazy='dynamic',
                                  backref=db.backref('roles', lazy='dynamic'))

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)

    def has_permission(self, perm_name):
        return self.permissions.filter_by(name=perm_name).first() is not None

    def add_permission(self, permission):
        if not self.has_permission(permission.name):
            self.permissions.append(permission)

    def remove_permission(self, permission):
        if self.has_permission(permission.name):
            self.permissions.remove(permission)
