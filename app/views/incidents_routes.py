from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.views.incidents import incidents
from app.models.incident import Incident
from app.models.category import Category
from app.models.user import User
from app.forms.incident_forms import IncidentForm, IncidentUpdateForm, IncidentReporterEditForm, IncidentAssignForm, IncidentCommentForm
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, ROLE_REPORTER, STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED

def is_valid_transition(current, target):
    # Strict workflow: Open -> In Progress -> Resolved -> Closed
    if current == target: return True
    if current == STATUS_OPEN and target == STATUS_IN_PROGRESS: return True
    if current == STATUS_IN_PROGRESS and target == STATUS_RESOLVED: return True
    if current == STATUS_RESOLVED and target == STATUS_CLOSED: return True
    return False

@incidents.route('/incidents')
@login_required
def list_incidents():
    if current_user.role == ROLE_REPORTER:
        query = Incident.query.filter_by(reporter_id=current_user.id)
    elif current_user.role == ROLE_AGENT:
        query = Incident.query.filter_by(assignee_id=current_user.id)
    else: 
        query = Incident.query
        
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    if status_filter: query = query.filter_by(status=status_filter)
    if priority_filter: query = query.filter_by(priority=priority_filter)
        
    incidents_list = query.order_by(Incident.created_at.desc()).all()
    return render_template('incidents/list.html', incidents=incidents_list)

@incidents.route('/incidents/create', methods=['GET', 'POST'])
@login_required
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
        db.session.commit()
        flash('Incident created successfully!', 'success')
        return redirect(url_for('incidents.view_incident', id=incident.id))
        
    return render_template('incidents/create.html', form=form)

@incidents.route('/incidents/<int:id>')
@login_required
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
        agents = User.query.filter_by(role=ROLE_AGENT).all()
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

@incidents.route('/incidents/<int:id>/update', methods=['POST'])
@login_required
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
                db.session.commit()
                flash('Incident updated successfully.', 'success')
        else:
            flash('Failed to update incident.', 'error')
            
    return redirect(url_for('incidents.view_incident', id=incident.id))

@incidents.route('/incidents/<int:id>/assign', methods=['POST'])
@login_required
def assign_incident(id):
    if current_user.role != ROLE_ADMIN:
        abort(403)
        
    incident = Incident.query.get_or_404(id)
    form = IncidentAssignForm()
    
    agents = User.query.filter_by(role=ROLE_AGENT).all()
    form.assignee_id.choices = [(0, 'Unassigned')] + [(a.id, a.username) for a in agents]
    
    if form.validate_on_submit():
        if form.assignee_id.data == 0:
            incident.assignee_id = None
            flash('Incident unassigned.', 'success')
        else:
            incident.assignee_id = form.assignee_id.data
            flash('Incident assigned successfully.', 'success')
        db.session.commit()
        
    return redirect(url_for('incidents.view_incident', id=incident.id))

@incidents.route('/incidents/<int:id>/comment', methods=['POST'])
@login_required
def comment_incident(id):
    from app.models.comment import Comment
    incident = Incident.query.get_or_404(id)
    
    if current_user.role == ROLE_REPORTER and incident.reporter_id != current_user.id:
        abort(403)
    if current_user.role == ROLE_AGENT and incident.assignee_id != current_user.id:
        abort(403)
        
    form = IncidentCommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            incident_id=incident.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully.', 'success')
    else:
        flash('Comment cannot be empty.', 'error')
        
    return redirect(url_for('incidents.view_incident', id=incident.id))


