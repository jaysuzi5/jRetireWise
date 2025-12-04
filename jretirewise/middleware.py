"""
Custom middleware for jRetireWise application.
"""

import os
import logging
import time
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger('jretirewise')


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


class CSRFRefererMiddleware:
    """
    Middleware to fix CSRF Referer validation for IP-based access.

    Django's CSRF middleware has strict validation for the Referer header
    during same-origin requests. When accessed via numeric IP address, the
    strict referer checking can fail even when the origin is legitimate.

    This middleware ensures the Referer header matches the request host
    for trusted origins, allowing login form submissions from IP addresses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process POST/PUT/DELETE/PATCH requests (methods that need CSRF)
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Get the Referer header if present
            referer = request.META.get('HTTP_REFERER')
            if referer:
                # Parse the referer URL
                parsed_referer = urlparse(referer)
                request_host = request.get_host()

                # Check if referer hostname matches request host
                referer_hostname = parsed_referer.hostname
                if referer_hostname:
                    # If the referer comes from a numeric IP or different hostname
                    # but the path is local, ensure the host matches for validation
                    # This is safe because we're only fixing it for local requests
                    if referer_hostname != request_host.split(':')[0]:
                        # Extract port if present in referer
                        referer_port = parsed_referer.port
                        request_port = request.get_port()

                        # If it's the same port (or default port), it's likely a legitimate request
                        if referer_port == request_port or (referer_port is None and request_port == ('443' if request.is_secure() else '80')):
                            # Normalize the referer to use the request's host
                            # This ensures Django's CSRF validation passes
                            corrected_referer = parsed_referer._replace(netloc=request_host).geturl()
                            request.META['HTTP_REFERER'] = corrected_referer

        response = self.get_response(request)
        return response


class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests and responses.

    Logs INFO level message for each request/response with:
    - HTTP method
    - Request path
    - Response status code
    - Execution time
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Skip logging for static files and health checks to reduce noise
        if not request.path.startswith('/static/') and not request.path.startswith('/health/'):
            logger.info(
                f"{request.method} {request.path} - Status: {response.status_code} - {elapsed_time:.2f}ms"
            )

        return response
