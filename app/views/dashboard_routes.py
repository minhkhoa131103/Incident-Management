from flask import render_template
from flask_login import login_required, current_user
from app.views.dashboard import dashboard
from app.utils.decorators import role_required
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED
from app.models.incident import Incident
from sqlalchemy import func

@dashboard.route('/')
@login_required
@role_required(ROLE_ADMIN, ROLE_AGENT)
def index():
    if current_user.role == ROLE_AGENT:
        base_query = Incident.query.filter_by(assignee_id=current_user.id)
    else:
        base_query = Incident.query
        
    stats = {
        'total': base_query.count(),
        'open': base_query.filter_by(status=STATUS_OPEN).count(),
        'in_progress': base_query.filter_by(status=STATUS_IN_PROGRESS).count(),
        'resolved': base_query.filter_by(status=STATUS_RESOLVED).count(),
        'closed': base_query.filter_by(status=STATUS_CLOSED).count(),
        'critical': base_query.filter_by(priority='Critical').count()
    }
    
    recent_incidents = base_query.order_by(Incident.updated_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', stats=stats, recent_incidents=recent_incidents)
