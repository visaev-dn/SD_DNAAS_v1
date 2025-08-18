#!/usr/bin/env python3
"""
API v1 Package
Version 1 of the Lab Automation API
"""

from flask import Blueprint

# Create the main v1 blueprint
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Import route modules to register them
from . import auth, bridge_domains, files, dashboard, configurations, deployments, devices, admin

__all__ = [
	'api_v1',
	'auth',
	'bridge_domains',
	'files',
	'dashboard',
	'configurations',
	'deployments',
	'devices',
	'admin'
]
