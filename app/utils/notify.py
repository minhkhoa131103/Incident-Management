from app import db
from app.models.notification import Notification

def create_notification(user_id, message, link=None):
    """
    Explicitly creates an in-app notification for a user.
    """
    notification = Notification(
        user_id=user_id,
        message=message,
        link=link
    )
    db.session.add(notification)
    # We rely on the calling route to do db.session.commit()
