from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.notification import Notification

notifications = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications.route('/')
@login_required
def list_notifications():
    user_notifications = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications/list.html', notifications=user_notifications)

@notifications.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        abort(403)
        
    notification.is_read = True
    db.session.commit()
    
    # Redirect to the link if provided
    if notification.link:
        return redirect(notification.link)
    return redirect(url_for('notifications.list_notifications'))

@notifications.route('/read_all', methods=['POST'])
@login_required
def mark_all_read():
    for notif in current_user.notifications.filter_by(is_read=False).all():
        notif.is_read = True
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))
