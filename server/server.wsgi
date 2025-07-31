#!/usr/bin/env python3
"""
Galaksio WSGI entry point for Apache/mod_wsgi
"""

import sys
import os

# Add the application directory to Python path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/server')

# Set environment variables
os.environ['PYTHONPATH'] = '/app'
os.environ['GALAKSIO_CONFIG'] = '/app/server/conf/serverconf.cfg'

# Import the Flask application
from server.server import app as application

if __name__ == '__main__':
    application.run()
