from flask import render_template, request
from flask_login import login_required, current_user
from app.views.dashboard import dashboard
from app.utils.decorators import permission_required
from app.utils.constants import ROLE_ADMIN, ROLE_AGENT, STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED
from app.models.incident import Incident
from app.models.user import User
from app.models.rbac import Role
from sqlalchemy import func
from datetime import datetime, timedelta

@dashboard.route('/')
@login_required
@permission_required('VIEW_DASHBOARD')
def index():
    # Base query scoped by role
    if current_user.role == ROLE_AGENT:
        role_query = Incident.query.filter_by(assignee_id=current_user.id)
    else:
        role_query = Incident.query
    
    # BUG-022: Date-range filtering via GET parameters
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    filtered_query = role_query
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            filtered_query = filtered_query.filter(Incident.created_at >= start_date)
        except ValueError:
            start_date_str = ''
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Include the entire end date by extending to start of next day
            end_date_bound = end_date + timedelta(days=1)
            filtered_query = filtered_query.filter(Incident.created_at < end_date_bound)
        except ValueError:
            end_date_str = ''
    
    # Primary stats (using date-filtered query)
    stats = {
        'total': filtered_query.count(),
        'open': filtered_query.filter_by(status=STATUS_OPEN).count(),
        'in_progress': filtered_query.filter_by(status=STATUS_IN_PROGRESS).count(),
        'resolved': filtered_query.filter_by(status=STATUS_RESOLVED).count(),
        'closed': filtered_query.filter_by(status=STATUS_CLOSED).count(),
        'critical': filtered_query.filter_by(priority='Critical').count()
    }
    
    # Average Resolution Time (approximate using created_at to updated_at for resolved/closed)
    resolved_incidents = filtered_query.filter(Incident.status.in_([STATUS_RESOLVED, STATUS_CLOSED])).all()
    if resolved_incidents:
        total_time = sum((inc.updated_at - inc.created_at).total_seconds() for inc in resolved_incidents)
        avg_seconds = total_time / len(resolved_incidents)
        avg_hours = round(avg_seconds / 3600, 1)
        stats['avg_resolution_hours'] = avg_hours
    else:
        stats['avg_resolution_hours'] = 0

    # Trend data: Last 7 days (always uses role-scoped query, not date-filtered)
    today = datetime.utcnow().date()
    trend_labels = []
    trend_data = []
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        trend_labels.append(target_date.strftime('%b %d'))
        
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)
        
        count = role_query.filter(Incident.created_at >= start_of_day, Incident.created_at < end_of_day).count()
        trend_data.append(count)
        
    trend = {
        'labels': trend_labels,
        'data': trend_data,
        'max': max(trend_data) if trend_data and max(trend_data) > 0 else 1
    }
    
    recent_incidents = filtered_query.order_by(Incident.updated_at.desc()).limit(5).all()
    
    # BUG-023: Aging incidents — Open or In Progress for > 7 days (uses role-scoped, not date-filtered)
    now_utc = datetime.utcnow()
    aging_threshold = now_utc - timedelta(days=7)
    aging_incidents = role_query.filter(
        Incident.status.in_([STATUS_OPEN, STATUS_IN_PROGRESS]),
        Incident.created_at < aging_threshold
    ).order_by(Incident.created_at.asc()).limit(10).all()
    aging_count = role_query.filter(
        Incident.status.in_([STATUS_OPEN, STATUS_IN_PROGRESS]),
        Incident.created_at < aging_threshold
    ).count()
    
    # BUG-023: Workload distribution by Agent (Admin only)
    workload = []
    if current_user.role == ROLE_ADMIN:
        agent_role = Role.query.filter_by(name=ROLE_AGENT).first()
        if agent_role:
            agents = User.query.filter_by(role_id=agent_role.id, is_active=True).all()
            for agent in agents:
                agent_total = Incident.query.filter_by(assignee_id=agent.id).count()
                agent_open = Incident.query.filter_by(assignee_id=agent.id, status=STATUS_OPEN).count()
                agent_in_progress = Incident.query.filter_by(assignee_id=agent.id, status=STATUS_IN_PROGRESS).count()
                agent_resolved = Incident.query.filter_by(assignee_id=agent.id).filter(
                    Incident.status.in_([STATUS_RESOLVED, STATUS_CLOSED])
                ).count()
                workload.append({
                    'username': agent.username,
                    'total': agent_total,
                    'open': agent_open,
                    'in_progress': agent_in_progress,
                    'resolved': agent_resolved
                })
    
    # Priority distribution (uses date-filtered query)
    priority_dist = {}
    for p in ['Low', 'Medium', 'High', 'Critical']:
        priority_dist[p] = filtered_query.filter_by(priority=p).count()
    
    return render_template('dashboard/index.html', 
                           stats=stats, 
                           recent_incidents=recent_incidents, 
                           trend=trend,
                           aging_incidents=aging_incidents,
                           aging_count=aging_count,
                           workload=workload,
                           priority_dist=priority_dist,
                           start_date=start_date_str,
                           end_date=end_date_str,
                           now_utc=now_utc)
