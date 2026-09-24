from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.views.incidents import incidents
from app.models.incident import Incident
from app.models.category import Category
from app.models.user import User
from app.forms.incident_forms import IncidentForm, IncidentUpdateForm, IncidentReporterEditForm, IncidentAssignForm, IncidentCommentForm
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, ROLE_REPORTER, STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED
from app.utils.decorators import permission_required
from app.utils.audit import log_action
from app.utils.notify import create_notification

def is_valid_transition(current, target):
    # Strict workflow: Open -> In Progress -> Resolved -> Closed
    if current == target: return True
    if current == STATUS_OPEN and target == STATUS_IN_PROGRESS: return True
    if current == STATUS_IN_PROGRESS and target == STATUS_RESOLVED: return True
    if current == STATUS_RESOLVED and target == STATUS_CLOSED: return True
    return False

@incidents.route('/incidents')
@login_required
@permission_required('VIEW_INCIDENT')
def list_incidents():
    if current_user.role == ROLE_REPORTER:
        query = Incident.query.filter_by(reporter_id=current_user.id)
    elif current_user.role == ROLE_AGENT:
        query = Incident.query.filter_by(assignee_id=current_user.id)
    else:
        query = Incident.query

    # BUG-021: Full filter support (status, priority, type, category, assignee, title search)
    status_filter    = request.args.get('status', '').strip()
    priority_filter  = request.args.get('priority', '').strip()
    type_filter      = request.args.get('type', '').strip()
    category_filter  = request.args.get('category_id', '').strip()
    assignee_filter  = request.args.get('assignee_id', '').strip()
    title_search     = request.args.get('title', '').strip()

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if type_filter:
        query = query.filter_by(type=type_filter)
    if category_filter:
        query = query.filter_by(category_id=int(category_filter))
    if assignee_filter:
        if assignee_filter == '0':
            query = query.filter(Incident.assignee_id.is_(None))
        else:
            query = query.filter_by(assignee_id=int(assignee_filter))
    if title_search:
        query = query.filter(Incident.title.ilike(f'%{title_search}%'))

    incidents_list = query.order_by(Incident.created_at.desc()).all()

    # Populate filter dropdowns — agents only for admin/agent views
    from app.models.rbac import Role as RoleModel
    categories = Category.query.order_by(Category.name).all()
    agents = []
    if current_user.role in [ROLE_ADMIN, ROLE_AGENT]:
        agent_role = RoleModel.query.filter_by(name=ROLE_AGENT).first()
        if agent_role:
            agents = User.query.filter_by(role_id=agent_role.id, is_active=True).all()

    return render_template('incidents/list.html', incidents=incidents_list,
                           categories=categories, agents=agents)

@incidents.route('/incidents/create', methods=['GET', 'POST'])
@login_required
@permission_required('CREATE_INCIDENT')
def create_incident():
    if current_user.role == ROLE_AGENT:
        abort(403)
        
    form = IncidentForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if form.validate_on_submit():
        incident = Incident(
            title=form.title.data,
            description=form.description.data,
            type=form.type.data,
            category_id=form.category_id.data,
            reporter_id=current_user.id
        )
        db.session.add(incident)
        db.session.flush()  # BUG-015: flush to get ID before logging
        log_action(current_user.id, 'CREATE_INCIDENT', 'Incident', incident.id, {'title': incident.title})
        db.session.commit()
        flash('Incident created successfully!', 'success')
        return redirect(url_for('incidents.view_incident', id=incident.id))
        
    return render_template('incidents/create.html', form=form)

@incidents.route('/incidents/<int:id>')
@login_required
@permission_required('VIEW_INCIDENT')
def view_incident(id):
    incident = Incident.query.get_or_404(id)
    
    if current_user.role == ROLE_REPORTER and incident.reporter_id != current_user.id:
        abort(403)
    if current_user.role == ROLE_AGENT and incident.assignee_id != current_user.id:
        abort(403)
        
    update_form = None
    edit_form = None
    assign_form = None
    categories = [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if current_user.role in [ROLE_AGENT, ROLE_ADMIN]:
        update_form = IncidentUpdateForm(obj=incident)
        update_form.category_id.choices = categories
        
    if current_user.role == ROLE_REPORTER and incident.status == STATUS_OPEN:
        edit_form = IncidentReporterEditForm(obj=incident)
        edit_form.category_id.choices = categories
        
    if current_user.role == ROLE_ADMIN:
        assign_form = IncidentAssignForm()
        from app.models.rbac import Role
        agent_role = Role.query.filter_by(name=ROLE_AGENT).first()
        # BUG-025: Only show active agents in the assignment dropdown
        agents = User.query.filter_by(role_id=agent_role.id, is_active=True).all() if agent_role else []
        assign_form.assignee_id.choices = [(0, 'Unassigned')] + [(a.id, a.username) for a in agents]
        if incident.assignee_id:
            assign_form.assignee_id.data = incident.assignee_id
            
    comment_form = IncidentCommentForm()
            
    return render_template('incidents/detail.html', 
                           incident=incident, 
                           update_form=update_form,
                           edit_form=edit_form,
                           assign_form=assign_form,
                           comment_form=comment_form)

# BUG-002: Added @permission_required('EDIT_INCIDENT')
@incidents.route('/incidents/<int:id>/update', methods=['POST'])
@login_required
@permission_required('EDIT_INCIDENT')
def update_incident(id):
    incident = Incident.query.get_or_404(id)
    categories = [(c.id, c.name) for c in Category.query.order_by('name')]
    
    if current_user.role == ROLE_REPORTER:
        if incident.reporter_id != current_user.id or incident.status != STATUS_OPEN:
            abort(403)
        form = IncidentReporterEditForm()
        form.category_id.choices = categories
        if form.validate_on_submit():
            incident.title = form.title.data
            incident.description = form.description.data
            incident.type = form.type.data
            incident.category_id = form.category_id.data
            # BUG-014: log_action BEFORE commit so it's part of the same transaction
            log_action(current_user.id, 'EDIT_INCIDENT', 'Incident', incident.id, {'title': incident.title})
            db.session.commit()
            flash('Incident updated successfully.', 'success')
        else:
            flash('Failed to update incident.', 'error')
            
    elif current_user.role in [ROLE_AGENT, ROLE_ADMIN]:
        if current_user.role == ROLE_AGENT and incident.assignee_id != current_user.id:
            abort(403)
        form = IncidentUpdateForm()
        form.category_id.choices = categories
        if form.validate_on_submit():
            target_status = form.status.data
            if target_status == STATUS_CLOSED and current_user.role != ROLE_ADMIN:
                flash('Only Admins can close incidents.', 'error')
            elif not is_valid_transition(incident.status, target_status):
                flash(f'Invalid status transition from {incident.status} to {target_status}.', 'error')
            else:
                incident.type = form.type.data
                incident.category_id = form.category_id.data
                incident.priority = form.priority.data
                incident.status = target_status
                # BUG-014: log_action BEFORE commit, include all changed fields in details
                log_action(current_user.id, 'UPDATE_INCIDENT', 'Incident', incident.id, 
                          {'status': target_status, 'priority': form.priority.data, 'type': form.type.data})
                link = url_for('incidents.view_incident', id=incident.id)
                if incident.reporter_id and incident.reporter_id != current_user.id:
                    create_notification(incident.reporter_id, f"Incident #{incident.id} status changed to {target_status}.", link)
                if incident.assignee_id and incident.assignee_id != current_user.id and incident.assignee_id != incident.reporter_id:
                    create_notification(incident.assignee_id, f"Incident #{incident.id} status changed to {target_status}.", link)
                db.session.commit()
                flash('Incident updated successfully.', 'success')
        else:
            flash('Failed to update incident.', 'error')
    else:
        # BUG-012: Explicitly deny custom roles that are not Reporter/Agent/Admin
        abort(403)
            
    return redirect(url_for('incidents.view_incident', id=incident.id))

@incidents.route('/incidents/<int:id>/assign', methods=['POST'])
@login_required
@permission_required('ASSIGN_INCIDENT')
def assign_incident(id):
    if current_user.role != ROLE_ADMIN:
        abort(403)
        
    incident = Incident.query.get_or_404(id)
    form = IncidentAssignForm()
    
    from app.models.rbac import Role
    agent_role = Role.query.filter_by(name=ROLE_AGENT).first()
    # BUG-025: Only show active agents
    agents = User.query.filter_by(role_id=agent_role.id, is_active=True).all() if agent_role else []
    form.assignee_id.choices = [(0, 'Unassigned')] + [(a.id, a.username) for a in agents]
    
    if form.validate_on_submit():
        # BUG-017: Track previous assignee for reassignment notification
        previous_assignee_id = incident.assignee_id
        link = url_for('incidents.view_incident', id=incident.id)
        
        if form.assignee_id.data == 0:
            incident.assignee_id = None
            flash('Incident unassigned.', 'success')
        else:
            incident.assignee_id = form.assignee_id.data
            flash('Incident assigned successfully.', 'success')
        
        # BUG-027: log_action BEFORE commit, always committed via single final commit
        log_action(current_user.id, 'ASSIGN_INCIDENT', 'Incident', incident.id, 
                  {'assignee_id': incident.assignee_id, 'previous_assignee_id': previous_assignee_id})
        
        # Notify the newly assigned agent
        if incident.assignee_id and incident.assignee_id != current_user.id:
            create_notification(incident.assignee_id, f"You have been assigned to Incident #{incident.id}.", link)
        
        # BUG-017: Notify the previous assignee about reassignment/unassignment
        if previous_assignee_id and previous_assignee_id != incident.assignee_id and previous_assignee_id != current_user.id:
            create_notification(previous_assignee_id, f"You have been unassigned from Incident #{incident.id}.", link)
        
        db.session.commit()
        
    return redirect(url_for('incidents.view_incident', id=incident.id))

# BUG-003: Added @permission_required('VIEW_INCIDENT')
@incidents.route('/incidents/<int:id>/comment', methods=['POST'])
@login_required
@permission_required('VIEW_INCIDENT')
def comment_incident(id):
    from app.models.comment import Comment
    incident = Incident.query.get_or_404(id)
    
    # Enforce ownership rules per role
    if current_user.role == ROLE_REPORTER and incident.reporter_id != current_user.id:
        abort(403)
    elif current_user.role == ROLE_AGENT and incident.assignee_id != current_user.id:
        abort(403)
    elif current_user.role not in [ROLE_REPORTER, ROLE_AGENT, ROLE_ADMIN]:
        # BUG-013: Explicitly deny custom roles
        abort(403)
        
    form = IncidentCommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            incident_id=incident.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        
        link = url_for('incidents.view_incident', id=incident.id)
        if incident.reporter_id and incident.reporter_id != current_user.id:
            create_notification(incident.reporter_id, f"New comment on Incident #{incident.id} by {current_user.username}.", link)
        if incident.assignee_id and incident.assignee_id != current_user.id and incident.assignee_id != incident.reporter_id:
            create_notification(incident.assignee_id, f"New comment on Incident #{incident.id} by {current_user.username}.", link)
        db.session.commit()
        flash('Comment added successfully.', 'success')
    else:
        flash('Comment cannot be empty.', 'error')
        
    return redirect(url_for('incidents.view_incident', id=incident.id))
