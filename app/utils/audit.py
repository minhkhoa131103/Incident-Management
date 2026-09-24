import json
from app import db
from app.models.audit import AuditLog

def log_action(user_id, action, resource_type, resource_id=None, details=None):
    """
    Explicitly logs an action to the AuditLog table.
    """
    details_str = json.dumps(details) if isinstance(details, dict) else details
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_str
    )
    db.session.add(log)
    # Note: We rely on the calling route to do db.session.commit()
    # to ensure the audit log is part of the same transaction.
