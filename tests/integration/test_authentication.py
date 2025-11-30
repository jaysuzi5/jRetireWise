"""
Integration tests for authentication views including logout functionality.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


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
