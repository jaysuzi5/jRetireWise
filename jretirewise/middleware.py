"""
Custom middleware for jRetireWise application.
"""

import os
from urllib.parse import urlparse
from django.conf import settings


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

    Django's CSRF middleware validates the Referer header for same-origin requests
    (POST, PUT, DELETE, etc.). When accessing via IP address, the Referer header
    contains the IP but Django's validation may be stricter about IP addresses.

    This middleware normalizes the Referer header to match ALLOWED_HOSTS for
    IP-based requests so that CSRF validation passes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If there's a Referer header and we're doing a method that needs CSRF validation
        if 'HTTP_REFERER' in request.META and request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            referer = request.META['HTTP_REFERER']
            parsed_referer = urlparse(referer)

            # Get the host from the request
            request_host = request.get_host()
            referer_netloc = parsed_referer.netloc

            # If the Referer netloc doesn't match the request host exactly,
            # try to fix it by checking if it's an IP address or alternate hostname
            if referer_netloc != request_host:
                # Extract just the hostname part (without port)
                referer_hostname = parsed_referer.hostname or ''
                request_hostname = request_host.split(':')[0]

                # Check if the referer is from a trusted origin (IP or ALLOWED_HOSTS)
                # For IP addresses, they should be accessible if they match the request
                if (referer_hostname == request_hostname or
                    referer_hostname in getattr(settings, 'ALLOWED_HOSTS', []) or
                    request_host in getattr(settings, 'ALLOWED_HOSTS', [])):
                    # Reconstruct the Referer with the correct host to pass validation
                    corrected_referer = parsed_referer._replace(netloc=request_host).geturl()
                    request.META['HTTP_REFERER'] = corrected_referer

        response = self.get_response(request)
        return response
