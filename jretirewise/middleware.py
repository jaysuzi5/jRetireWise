"""
Custom middleware for jRetireWise application.
"""

import os


class ForceScriptNameMiddleware:
    """
    Middleware to set SCRIPT_NAME in WSGI environ for correct URL generation.

    When Django is deployed at a subpath (e.g., /jretirewise/), we need to tell
    Django about this base path so it can generate correct URLs in redirects,
    reverse() calls, and template tags. SCRIPT_NAME is used by Django to track
    the prefix where the application is mounted.

    With our current Ingress setup:
    - Ingress routes /jretirewise/* directly to Django (no path rewriting)
    - Django URL patterns include the /jretirewise/ prefix
    - We also need to set SCRIPT_NAME=/jretirewise so Django knows the base path
      for URL generation (otherwise redirects and reverse() won't include the prefix)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Always set SCRIPT_NAME to /jretirewise for Kubernetes subpath deployment
        self.script_name = '/jretirewise'

    def __call__(self, request):
        # Set SCRIPT_NAME so Django generates URLs with the /jretirewise/ prefix
        request.META['SCRIPT_NAME'] = self.script_name

        response = self.get_response(request)
        return response
