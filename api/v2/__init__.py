# API Version 2 Blueprint
# Future API version with enhanced features and backward compatibility

from flask import Blueprint

api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# Import route modules when they are created
# from . import auth, bridge_domains, files, dashboard, configurations, deployments, devices, admin

__all__ = ['api_v2']
