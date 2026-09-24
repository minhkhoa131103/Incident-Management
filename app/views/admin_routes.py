from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.views.admin import admin
from app.models.user import User
from app.models.category import Category
from app.models.rbac import Role, Permission
from app.models.incident import Incident
from app.models.comment import Comment
from app.models.audit import AuditLog
from app.models.notification import Notification
from app.forms.admin_forms import AdminUserForm, AdminUserEditForm, AdminCategoryForm, AdminRoleForm
from app.utils.decorators import permission_required
from app.utils.audit import log_action

@admin.route('/users', methods=['GET', 'POST'])
@login_required
@permission_required('MANAGE_USERS')
def list_users():
    form = AdminUserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by('name')]
    
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role_id=form.role_id.data
            )
            user.password = form.password.data
            db.session.add(user)
            db.session.commit()
            log_action(current_user.id, 'CREATE_USER', 'User', user.id, {'username': user.username})
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.list_users'))
            
    users = User.query.order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users, form=form)

@admin.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('MANAGE_USERS')
def edit_user(id):
    user = User.query.get_or_404(id)
    form = AdminUserEditForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by('name')]
    
    if form.validate_on_submit():
        # BUG-009: Prevent admin from changing their own role
        if user.id == current_user.id and form.role_id.data != user.role_id:
            flash('You cannot change your own role.', 'error')
            return redirect(url_for('admin.edit_user', id=id))
        if User.query.filter(User.username == form.username.data, User.id != id).first():
            flash('Username already exists.', 'error')
        elif User.query.filter(User.email == form.email.data, User.id != id).first():
            flash('Email already exists.', 'error')
        else:
            user.username = form.username.data
            user.email = form.email.data
            user.role_id = form.role_id.data
            if form.password.data:
                user.password = form.password.data
            db.session.commit()
            log_action(current_user.id, 'EDIT_USER', 'User', user.id, {'username': user.username})
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.list_users'))
            
    return render_template('admin/user_edit.html', form=form, user=user)

@admin.route('/users/<int:id>/toggle', methods=['POST'])
@login_required
@permission_required('MANAGE_USERS')
def toggle_user(id):
    user = User.query.get_or_404(id)
    # BUG-008: Prevent admin from disabling their own account
    if user.id == current_user.id:
        flash('You cannot disable your own account.', 'error')
        return redirect(url_for('admin.list_users'))
    user.is_active = not user.is_active
    log_action(current_user.id, 'TOGGLE_USER_STATUS', 'User', user.id, {'is_active': user.is_active})
    db.session.commit()
    status = "enabled" if user.is_active else "disabled"
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.list_users'))

@admin.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('MANAGE_USERS')
def delete_user(id):
    user = User.query.get_or_404(id)
    # BUG-008: Prevent admin from deleting their own account
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.list_users'))
    
    # Check ALL FK relationships (BUG-004)
    has_incidents = Incident.query.filter((Incident.reporter_id == id) | (Incident.assignee_id == id)).first() is not None
    has_comments = Comment.query.filter_by(user_id=id).first() is not None
    has_audit_logs = AuditLog.query.filter_by(user_id=id).first() is not None
    has_notifications = Notification.query.filter_by(user_id=id).first() is not None
    
    if has_incidents or has_comments or has_audit_logs or has_notifications:
        flash(f'Cannot hard delete user {user.username} because they have related records (Incidents, Comments, Audit Logs, or Notifications). Please disable the account instead.', 'error')
    else:
        username = user.username
        db.session.delete(user)
        log_action(current_user.id, 'DELETE_USER', 'User', id, {'username': username})
        db.session.commit()
        flash(f'User {username} has been permanently deleted.', 'success')
        
    return redirect(url_for('admin.list_users'))

# BUG-024: Category management uses its own dedicated MANAGE_CATEGORIES permission
@admin.route('/categories', methods=['GET', 'POST'])
@login_required
@permission_required('MANAGE_CATEGORIES')
def list_categories():
    form = AdminCategoryForm()
    if form.validate_on_submit():
        if Category.query.filter_by(name=form.name.data).first():
            flash('Category already exists.', 'error')
        else:
            category = Category(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(category)
            log_action(current_user.id, 'CREATE_CATEGORY', 'Category', None, {'name': category.name})
            db.session.commit()
            flash('Category created successfully.', 'success')
            return redirect(url_for('admin.list_categories'))
            
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories, form=form)

# BUG-029: Added pagination (50 entries/page) and optional action + actor filters
@admin.route('/audit')
@login_required
@permission_required('VIEW_AUDIT_LOGS')
def list_audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    actor_filter = request.args.get('actor', '').strip()

    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f'%{action_filter}%'))
    if actor_filter:
        # Join User to filter by username
        query = query.join(User, AuditLog.user_id == User.id, isouter=True).filter(
            User.username.ilike(f'%{actor_filter}%')
        )

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    logs = pagination.items
    return render_template('admin/audit.html', logs=logs, pagination=pagination,
                           action_filter=action_filter, actor_filter=actor_filter)

# BUG-011: Role Management
@admin.route('/roles', methods=['GET'])
@login_required
@permission_required('MANAGE_ROLES')
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', roles=roles)

@admin.route('/roles/create', methods=['GET', 'POST'])
@login_required
@permission_required('MANAGE_ROLES')
def create_role():
    form = AdminRoleForm()
    permissions = Permission.query.order_by(Permission.name).all()
    
    if form.validate_on_submit():
        if Role.query.filter_by(name=form.name.data).first():
            flash('Role name already exists.', 'error')
        else:
            role = Role(name=form.name.data, description=form.description.data, is_system=False)
            db.session.add(role)
            
            selected_perms = request.form.getlist('permissions')
            for perm_id in selected_perms:
                perm = Permission.query.get(int(perm_id))
                if perm:
                    role.add_permission(perm)
            
            db.session.commit()
            log_action(current_user.id, 'CREATE_ROLE', 'Role', role.id, {'name': role.name})
            flash('Role created successfully.', 'success')
            return redirect(url_for('admin.list_roles'))
            
    return render_template('admin/role_form.html', form=form, permissions=permissions, role=None, role_perm_ids=[])

@admin.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('MANAGE_ROLES')
def edit_role(id):
    role = Role.query.get_or_404(id)
    form = AdminRoleForm(obj=role)
    permissions = Permission.query.order_by(Permission.name).all()
    
    if form.validate_on_submit():
        # Prevent editing name of system roles
        if role.is_system and form.name.data != role.name:
            flash('Cannot change the name of a system role.', 'error')
            form.name.data = role.name
        elif not role.is_system and Role.query.filter(Role.name == form.name.data, Role.id != id).first():
            flash('Role name already exists.', 'error')
        else:
            if not role.is_system:
                role.name = form.name.data
                
                # Update permissions
                selected_perms = request.form.getlist('permissions')
                selected_perm_ids = [int(p) for p in selected_perms]
                
                # Remove unselected
                for perm in role.permissions.all():
                    if perm.id not in selected_perm_ids:
                        role.remove_permission(perm)
                
                # Add newly selected
                current_perm_ids = [p.id for p in role.permissions.all()]
                for perm_id in selected_perm_ids:
                    if perm_id not in current_perm_ids:
                        perm = Permission.query.get(perm_id)
                        if perm:
                            role.add_permission(perm)
            
            role.description = form.description.data
            db.session.commit()
            log_action(current_user.id, 'EDIT_ROLE', 'Role', role.id, {'name': role.name})
            flash('Role updated successfully.', 'success')
            return redirect(url_for('admin.list_roles'))
            
    # Pre-select permissions for GET
    role_perm_ids = [p.id for p in role.permissions.all()]
    return render_template('admin/role_form.html', form=form, permissions=permissions, role=role, role_perm_ids=role_perm_ids)

@admin.route('/roles/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('MANAGE_ROLES')
def delete_role(id):
    role = Role.query.get_or_404(id)
    if role.is_system:
        flash('Cannot delete a system role.', 'error')
    elif User.query.filter_by(role_id=role.id).first():
        flash('Cannot delete role because it is assigned to one or more users.', 'error')
    else:
        role_name = role.name
        db.session.delete(role)
        log_action(current_user.id, 'DELETE_ROLE', 'Role', id, {'name': role_name})
        db.session.commit()
        flash(f'Role {role_name} has been deleted.', 'success')
    return redirect(url_for('admin.list_roles'))
