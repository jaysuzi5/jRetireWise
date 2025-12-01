"""
Custom middleware for jRetireWise application.
"""

import os


class ForceScriptNameMiddleware:
    """
    Middleware to set SCRIPT_NAME in WSGI environ based on FORCE_SCRIPT_NAME setting.

    This is needed for Django deployments behind a reverse proxy (like Nginx Ingress)
    that rewrites the path. The Ingress rewrites /jretirewise/* to /*, so Django
    doesn't know it's being served at /jretirewise/. This middleware tells Django
    about the actual base path so it can generate correct URLs.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Get FORCE_SCRIPT_NAME from environment
        self.script_name = os.environ.get('FORCE_SCRIPT_NAME', '')

    def __call__(self, request):
        # If FORCE_SCRIPT_NAME is set, update SCRIPT_NAME in request
        if self.script_name:
            request.META['SCRIPT_NAME'] = self.script_name

        response = self.get_response(request)
        return response
