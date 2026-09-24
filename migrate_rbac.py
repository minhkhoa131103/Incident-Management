from app import create_app, db
from app.models.user import User
from app.models.rbac import Role, Permission
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, ROLE_REPORTER

app = create_app()

PERMISSIONS = [
    'VIEW_INCIDENT',
    'CREATE_INCIDENT',
    'EDIT_INCIDENT',
    'UPDATE_INCIDENT_STATUS',
    'ASSIGN_INCIDENT',
    'MANAGE_USERS',
    'MANAGE_ROLES',
    'MANAGE_CATEGORIES',
    'VIEW_AUDIT_LOGS',
    'VIEW_DASHBOARD'
]

ROLE_PERMISSIONS = {
    ROLE_ADMIN: PERMISSIONS,
    ROLE_AGENT: ['VIEW_INCIDENT', 'UPDATE_INCIDENT_STATUS', 'VIEW_DASHBOARD'],
    ROLE_REPORTER: ['VIEW_INCIDENT', 'CREATE_INCIDENT', 'EDIT_INCIDENT']
}

def run_migration():
    with app.app_context():
        # 1. Create permissions
        perms_dict = {}
        for p_name in PERMISSIONS:
            perm = Permission.query.filter_by(name=p_name).first()
            if not perm:
                perm = Permission(name=p_name)
                db.session.add(perm)
            perms_dict[p_name] = perm
        db.session.commit()
        
        # 2. Create roles and assign permissions
        roles_dict = {}
        for r_name, p_names in ROLE_PERMISSIONS.items():
            role = Role.query.filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name, is_system=True)
                db.session.add(role)
            db.session.commit()
            
            # Reset and assign permissions
            role.permissions = []
            for p_name in p_names:
                role.add_permission(perms_dict[p_name])
            roles_dict[r_name] = role
        db.session.commit()
        
        # 3. Map users
        users = User.query.all()
        for user in users:
            if user.role in roles_dict:
                user.role_id = roles_dict[user.role].id
        db.session.commit()
        
        print("Data migration for RBAC completed successfully!")

if __name__ == '__main__':
    run_migration()
