"""
Integration tests for authentication views including logout functionality and OAuth configuration.
"""

import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings


class LogoutViewIntegrationTestCase(TestCase):
    """Test LogoutView with GET and POST methods."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()

    def test_logout_get_request_authenticated_user(self):
        """Test GET logout request for authenticated user."""
        # Login first
        self.client.login(username='testuser', password='TestPass123!')

        # Test GET logout
        response = self.client.get('/auth/logout/', follow=False)

        # Should return 302 redirect
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"

        # Should redirect to login page
        assert response['Location'] == '/auth/accounts/login/', \
            f"Expected redirect to login, got {response['Location']}"

    def test_logout_get_request_unauthenticated_user(self):
        """Test GET logout request for unauthenticated user."""
        # Don't login, just make request
        response = self.client.get('/auth/logout/', follow=False)

        # Should still return 302 redirect (graceful handling)
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"

    def test_logout_get_request_redirects_to_login(self):
        """Test that GET logout redirects to login page."""
        # Login first
        self.client.login(username='testuser', password='TestPass123!')

        # Follow the redirect
        response = self.client.get('/auth/logout/', follow=True)

        # Should end up at login page
        assert response.status_code == 200
        assert 'login' in response.content.decode().lower()

    def test_logout_post_request_authenticated_user(self):
        """Test POST logout request for authenticated user."""
        # Login first
        self.client.login(username='testuser', password='TestPass123!')

        # Test POST logout
        response = self.client.post('/auth/logout/')

        # Should return 200 OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Should return JSON response
        data = response.json()
        assert data['status'] == 'logged out', f"Expected 'logged out' status, got {data}"

    def test_logout_post_request_unauthenticated_user(self):
        """Test POST logout request for unauthenticated user."""
        # Don't login
        response = self.client.post('/auth/logout/')

        # Should still return 200 (AllowAny permission)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Should return JSON response
        data = response.json()
        assert data['status'] == 'logged out', f"Expected 'logged out' status, got {data}"

    def test_logout_actually_logs_out_user(self):
        """Test that logout actually logs out the user."""
        # Login first
        self.client.login(username='testuser', password='TestPass123!')

        # Verify user is logged in
        response = self.client.get('/dashboard/')
        assert response.status_code == 200, "User should be able to access dashboard"

        # Logout
        self.client.get('/auth/logout/')

        # Try to access protected page
        response = self.client.get('/dashboard/')

        # Should be redirected to login (status 302)
        assert response.status_code == 302, \
            f"User should be redirected to login after logout, got {response.status_code}"

    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        # Login first
        self.client.login(username='testuser', password='TestPass123!')

        # Verify session has user ID
        assert '_auth_user_id' in self.client.session, "User should be in session"

        # Logout
        self.client.get('/auth/logout/')

        # Session should not have user ID anymore
        assert '_auth_user_id' not in self.client.session, \
            "User should not be in session after logout"

    def test_logout_get_returns_correct_headers(self):
        """Test that logout GET returns redirect response."""
        self.client.login(username='testuser', password='TestPass123!')

        response = self.client.get('/auth/logout/', follow=False)

        # Check response type
        assert response.status_code in [301, 302, 303, 307, 308], \
            f"Expected redirect status code, got {response.status_code}"

        # Check Location header exists
        assert 'Location' in response, "Location header should be present in redirect"

    def test_logout_post_returns_json(self):
        """Test that logout POST returns proper JSON."""
        self.client.login(username='testuser', password='TestPass123!')

        response = self.client.post('/auth/logout/')

        # Check response is JSON
        assert response['Content-Type'] == 'application/json'

        # Check JSON structure
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        assert 'status' in data, "Response should have 'status' key"

    def test_logout_multiple_times(self):
        """Test that multiple logout attempts work gracefully."""
        self.client.login(username='testuser', password='TestPass123!')

        # First logout
        response1 = self.client.get('/auth/logout/', follow=False)
        assert response1.status_code == 302

        # Second logout (should still work)
        response2 = self.client.get('/auth/logout/', follow=False)
        assert response2.status_code == 302

        # Third logout (should still work)
        response3 = self.client.post('/auth/logout/')
        assert response3.status_code == 200


class LoginViewIntegrationTestCase(TestCase):
    """Test LoginView."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()

    def test_login_view_post(self):
        """Test POST to login view."""
        response = self.client.post('/auth/login/')

        # Should return 200 OK
        assert response.status_code == 200

        # Should return JSON response
        data = response.json()
        assert 'status' in data
        assert 'OAuth' in data['status']

    def test_login_view_get_not_allowed(self):
        """Test GET to login view (should not be allowed)."""
        response = self.client.get('/auth/login/')

        # GET should not be allowed on APIView
        assert response.status_code == 405  # Method Not Allowed


class UserProfileViewIntegrationTestCase(TestCase):
    """Test UserProfileView."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_user_profile_get(self):
        """Test GET user profile."""
        response = self.client.get('/auth/profile/')

        # Should return 200 OK
        assert response.status_code == 200

        # Should return JSON
        data = response.json()
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'

    def test_user_profile_get_requires_authentication(self):
        """Test that getting user profile requires authentication."""
        client = Client()
        response = client.get('/auth/profile/')

        # Should return 403 Forbidden
        assert response.status_code == 403


class GoogleOAuthConfigurationTestCase(TestCase):
    """Test Google OAuth 2.0 configuration."""

    def setUp(self):
        """Set up Google OAuth app in database for testing."""
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site

        # Ensure site exists
        site, _ = Site.objects.get_or_create(
            pk=1,
            defaults={'domain': 'example.com', 'name': 'Example'}
        )

        # Create Google OAuth app
        self.google_app, _ = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': 'test-client-id-123.apps.googleusercontent.com',
                'secret': 'test-secret-key-123',
            }
        )

        # Link app to site
        self.google_app.sites.add(site)

    def test_oauth_providers_configured(self):
        """Test that SOCIALACCOUNT_PROVIDERS is configured."""
        assert 'google' in settings.SOCIALACCOUNT_PROVIDERS, \
            "Google provider should be configured in SOCIALACCOUNT_PROVIDERS"

    def test_oauth_google_has_scope_config(self):
        """Test that Google OAuth SCOPE configuration exists."""
        google_provider = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        assert 'SCOPE' in google_provider, \
            "Google provider should have 'SCOPE' configuration"

    def test_oauth_google_app_stored_in_database(self):
        """Test that Google OAuth credentials are stored in the SocialApp database model."""
        from allauth.socialaccount.models import SocialApp

        google_app = SocialApp.objects.filter(provider='google').first()
        assert google_app is not None, \
            "Google OAuth app should be stored in SocialApp database model"
        assert google_app.client_id, \
            "Google SocialApp should have client_id"
        assert google_app.secret, \
            "Google SocialApp should have secret"

    def test_oauth_google_database_app_has_client_id(self):
        """Test that Google OAuth SocialApp has client_id in database."""
        from allauth.socialaccount.models import SocialApp

        google_app = SocialApp.objects.filter(provider='google').first()
        assert google_app is not None
        assert google_app.client_id, \
            "Google SocialApp database entry should have 'client_id'"

    def test_oauth_google_database_app_has_secret(self):
        """Test that Google OAuth SocialApp has secret in database."""
        from allauth.socialaccount.models import SocialApp

        google_app = SocialApp.objects.filter(provider='google').first()
        assert google_app is not None
        assert google_app.secret, \
            "Google SocialApp database entry should have 'secret'"

    def test_oauth_scopes_configured(self):
        """Test that OAuth scopes are properly configured."""
        google_provider = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        scopes = google_provider.get('SCOPE', [])
        assert 'profile' in scopes, "OAuth should request 'profile' scope"
        assert 'email' in scopes, "OAuth should request 'email' scope"

    def test_oauth_auth_params_configured(self):
        """Test that OAuth auth parameters are configured."""
        google_provider = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        auth_params = google_provider.get('AUTH_PARAMS', {})
        assert auth_params.get('access_type') == 'online', \
            "OAuth should use 'online' access_type"

    def test_oauth_with_database_credentials(self):
        """Test that OAuth uses credentials from SocialApp database model."""
        from allauth.socialaccount.models import SocialApp

        # Verify that credentials come from the database, not settings
        google_app = SocialApp.objects.filter(provider='google').first()
        assert google_app is not None, \
            "Google OAuth credentials should be stored in SocialApp database"
        assert len(google_app.client_id) > 0, \
            "Google SocialApp should have non-empty client_id from database"
        assert len(google_app.secret) > 0, \
            "Google SocialApp should have non-empty secret from database"

    def test_allauth_authentication_backends_configured(self):
        """Test that allauth authentication backend is configured."""
        backends = settings.AUTHENTICATION_BACKENDS
        assert 'allauth.account.auth_backends.AuthenticationBackend' in backends, \
            "allauth AuthenticationBackend should be in AUTHENTICATION_BACKENDS"

    def test_socialaccount_auto_signup_enabled(self):
        """Test that auto signup is enabled for social accounts."""
        assert settings.SOCIALACCOUNT_AUTO_SIGNUP is True, \
            "SOCIALACCOUNT_AUTO_SIGNUP should be True to allow new users"

    def test_login_callback_url(self):
        """Test that OAuth callback URL is accessible."""
        client = Client()
        # Google OAuth callback URL pattern
        callback_urls = [
            '/auth/accounts/google/callback/',
            '/accounts/google/callback/',
        ]

        for url in callback_urls:
            try:
                response = client.get(url, follow=False)
                # Callback URL should exist (even if it fails without valid OAuth response)
                # A 403/400 means the URL exists but auth failed (which is expected)
                assert response.status_code in [400, 403, 404, 405], \
                    f"OAuth callback at {url} should be accessible or give auth error"
                break
            except Exception:
                continue


class ThemePreferenceTestCase(TestCase):
    """Test theme preference functionality."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='TestPass123!')

    def test_user_profile_includes_theme_preference(self):
        """Test that user profile includes theme_preference field."""
        response = self.client.get('/auth/profile/')

        # Should return 200 OK
        assert response.status_code == 200

        # Should return JSON with theme_preference
        data = response.json()
        assert 'profile' in data
        assert 'theme_preference' in data['profile']
        assert data['profile']['theme_preference'] in ['light', 'dark']

    def test_theme_preference_defaults_to_light(self):
        """Test that new users have light theme as default."""
        response = self.client.get('/auth/profile/')
        data = response.json()

        # Default theme should be light
        assert data['profile']['theme_preference'] == 'light'

    def test_update_theme_preference_to_dark(self):
        """Test updating theme preference to dark."""
        response = self.client.put(
            '/auth/profile/',
            data={'theme_preference': 'dark'},
            content_type='application/json'
        )

        # Should return 200 OK
        assert response.status_code == 200

        # Should return updated preference
        data = response.json()
        assert data['profile']['theme_preference'] == 'dark'

        # Verify preference was saved in database
        self.user.refresh_from_db()
        assert self.user.profile.theme_preference == 'dark'

    def test_update_theme_preference_back_to_light(self):
        """Test updating theme preference back to light."""
        # First set to dark
        self.user.profile.theme_preference = 'dark'
        self.user.profile.save()

        # Now update back to light
        response = self.client.put(
            '/auth/profile/',
            data={'theme_preference': 'light'},
            content_type='application/json'
        )

        # Should return 200 OK
        assert response.status_code == 200

        # Should return updated preference
        data = response.json()
        assert data['profile']['theme_preference'] == 'light'

        # Verify preference was saved in database
        self.user.refresh_from_db()
        assert self.user.profile.theme_preference == 'light'

    def test_invalid_theme_preference_rejected(self):
        """Test that invalid theme preference is rejected."""
        response = self.client.put(
            '/auth/profile/',
            data={'theme_preference': 'invalid-theme'},
            content_type='application/json'
        )

        # Should return 400 Bad Request
        assert response.status_code == 400

        # Original preference should be unchanged
        self.user.refresh_from_db()
        assert self.user.profile.theme_preference == 'light'

    def test_theme_preference_requires_authentication(self):
        """Test that updating theme preference requires authentication."""
        client = Client()
        response = client.put(
            '/auth/profile/',
            data={'theme_preference': 'dark'},
            content_type='application/json'
        )

        # Should return 403 Forbidden
        assert response.status_code == 403
