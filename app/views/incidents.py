from flask import Blueprint

incidents = Blueprint('incidents', __name__)

from . import incidents_routes
