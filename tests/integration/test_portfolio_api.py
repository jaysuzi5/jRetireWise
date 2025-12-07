"""
Integration tests for Phase 2.0 Advanced Portfolio Management API endpoints.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from jretirewise.financial.models import Portfolio, Account, AccountValueHistory, PortfolioSnapshot


class PortfolioAPIIntegrationTestCase(TestCase):
    """Integration tests for Portfolio API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name='Test Portfolio'
        )

    def test_portfolio_list(self):
        """Test portfolio list endpoint."""
        response = self.client.get('/api/v1/portfolios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response might be paginated, so check for results key
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertGreater(len(data), 0)
        # Find our test portfolio
        portfolios = [p for p in data if p['id'] == self.portfolio.id]
        self.assertEqual(len(portfolios), 1)
        self.assertEqual(portfolios[0]['name'], 'Test Portfolio')

    def test_portfolio_create(self):
        """Test portfolio creation endpoint."""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)

        data = {
            'name': 'New Portfolio',
            'description': 'A test portfolio'
        }
        response = self.client.post('/api/v1/portfolios/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Portfolio')
        self.assertEqual(response.data['account_count'], 0)
        self.assertEqual(response.data['total_value'], 0.0)

    def test_portfolio_retrieve(self):
        """Test portfolio detail endpoint."""
        response = self.client.get(f'/api/v1/portfolios/{self.portfolio.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Portfolio')
        self.assertIn('accounts', response.data)
        self.assertIn('snapshots', response.data)

    def test_portfolio_update(self):
        """Test portfolio update endpoint."""
        data = {'name': 'Updated Portfolio'}
        response = self.client.patch(
            f'/api/v1/portfolios/{self.portfolio.id}/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Portfolio')

    def test_portfolio_delete(self):
        """Test portfolio deletion endpoint."""
        response = self.client.delete(f'/api/v1/portfolios/{self.portfolio.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Portfolio.objects.filter(id=self.portfolio.id).exists())

    def test_portfolio_summary_action(self):
        """Test portfolio summary action."""
        response = self.client.get(f'/api/v1/portfolios/{self.portfolio.id}/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name', response.data)
        self.assertIn('accounts', response.data)
        self.assertIn('total_value', response.data)

    def test_portfolio_accounts_by_type_action(self):
        """Test portfolio accounts_by_type action."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Savings',
            current_value=Decimal('10000.00')
        )
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='roth_ira',
            account_name='Roth IRA',
            current_value=Decimal('50000.00')
        )

        response = self.client.get(
            f'/api/v1/portfolios/{self.portfolio.id}/accounts_by_type/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Savings Account', response.data)
        self.assertIn('Roth IRA', response.data)

    def test_portfolio_only_own_portfolios(self):
        """Test user can only see their own portfolios."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_portfolio = Portfolio.objects.create(
            user=other_user,
            name='Other Portfolio'
        )

        response = self.client.get('/api/v1/portfolios/')
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Should only see our portfolio
        user_portfolios = [p for p in data if p['user'] == self.user.id]
        self.assertGreaterEqual(len(user_portfolios), 1)
        # Should not see other user's portfolio
        other_portfolios = [p for p in data if p['user'] == other_user.id]
        self.assertEqual(len(other_portfolios), 0)


class AccountAPIIntegrationTestCase(TestCase):
    """Integration tests for Account API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Test Savings',
            current_value=Decimal('10000.00')
        )

    def test_account_list(self):
        """Test account list endpoint."""
        response = self.client.get('/api/v1/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Find our test account
        test_accounts = [a for a in data if a['id'] == self.account.id]
        self.assertEqual(len(test_accounts), 1)
        self.assertEqual(test_accounts[0]['account_name'], 'Test Savings')

    def test_account_create(self):
        """Test account creation endpoint."""
        data = {
            'portfolio': self.portfolio.id,
            'account_type': 'roth_ira',
            'account_name': 'New Roth IRA',
            'current_value': '50000.00',
            'default_growth_rate': '0.07'
        }
        response = self.client.post('/api/v1/accounts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['account_name'], 'New Roth IRA')
        self.assertEqual(float(response.data['current_value']), 50000.00)

    def test_account_retrieve(self):
        """Test account detail endpoint."""
        response = self.client.get(f'/api/v1/accounts/{self.account.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_name'], 'Test Savings')
        self.assertIn('value_history', response.data)
        self.assertIn('recent_history', response.data)

    def test_account_update(self):
        """Test account update endpoint."""
        data = {
            'account_name': 'Updated Savings',
            'current_value': '15000.00'
        }
        response = self.client.patch(f'/api/v1/accounts/{self.account.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['account_name'], 'Updated Savings')
        self.assertEqual(float(response.data['current_value']), 15000.00)

    def test_account_delete(self):
        """Test account deletion endpoint."""
        response = self.client.delete(f'/api/v1/accounts/{self.account.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Account.objects.filter(id=self.account.id).exists())

    def test_account_filter_by_status(self):
        """Test account filtering by status."""
        Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Closed Savings',
            status='closed'
        )

        response = self.client.get('/api/v1/accounts/?status=active')
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Filter to just our test portfolio's active accounts
        active_accounts = [a for a in data if a['portfolio'] == self.portfolio.id and a['status'] == 'active']
        self.assertGreater(len(active_accounts), 0)
        for account in active_accounts:
            self.assertEqual(account['status'], 'active')

    def test_account_record_value_action(self):
        """Test account record_value action."""
        data = {
            'account': self.account.id,
            'value': '12000.00',
            'recorded_date': date.today().isoformat(),
            'source': 'manual',
            'notes': 'Monthly update'
        }
        response = self.client.post(
            f'/api/v1/accounts/{self.account.id}/record_value/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['value']), 12000.00)

    def test_account_history_action(self):
        """Test account history action."""
        AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('10000.00'),
            recorded_date=date.today(),
            recorded_by=self.user
        )

        response = self.client.get(f'/api/v1/accounts/{self.account.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['value']), 10000.00)

    def test_account_effective_metrics_action(self):
        """Test account effective_metrics action."""
        response = self.client.get(
            f'/api/v1/accounts/{self.account.id}/effective_metrics/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('effective_growth_rate', response.data)
        self.assertIn('annual_contribution', response.data)
        self.assertTrue(response.data['is_active'])


class AccountValueHistoryAPIIntegrationTestCase(TestCase):
    """Integration tests for AccountValueHistory API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='savings',
            account_name='Test Savings'
        )
        self.history = AccountValueHistory.objects.create(
            account=self.account,
            value=Decimal('10000.00'),
            recorded_date=date.today(),
            recorded_by=self.user,
            source='manual'
        )

    def test_history_list(self):
        """Test account history list endpoint."""
        response = self.client.get('/api/v1/account-history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Find our test history
        test_history = [h for h in data if h['id'] == self.history.id]
        self.assertEqual(len(test_history), 1)
        self.assertEqual(float(test_history[0]['value']), 10000.00)

    def test_history_create(self):
        """Test history creation endpoint."""
        data = {
            'account': self.account.id,
            'value': '12000.00',
            'recorded_date': date.today().isoformat(),
            'source': 'manual',
            'notes': 'New entry'
        }
        response = self.client.post('/api/v1/account-history/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['value']), 12000.00)

    def test_history_retrieve(self):
        """Test history detail endpoint."""
        response = self.client.get(f'/api/v1/account-history/{self.history.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['value']), 10000.00)

    def test_history_filter_by_account(self):
        """Test history filtering by account."""
        other_account = Account.objects.create(
            portfolio=self.portfolio,
            account_type='roth_ira',
            account_name='Other Account'
        )
        AccountValueHistory.objects.create(
            account=other_account,
            value=Decimal('50000.00'),
            recorded_date=date.today(),
            recorded_by=self.user
        )

        response = self.client.get(f'/api/v1/account-history/?account={self.account.id}')
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # All should belong to our account
        for hist in data:
            self.assertEqual(hist['account'], self.account.id)
        # Should have at least our test history
        self.assertGreater(len(data), 0)


class PortfolioSnapshotAPIIntegrationTestCase(TestCase):
    """Integration tests for PortfolioSnapshot API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.snapshot = PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('100000.00'),
            snapshot_date=date.today()
        )

    def test_snapshot_list(self):
        """Test snapshot list endpoint."""
        response = self.client.get('/api/v1/portfolio-snapshots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Find our test snapshot
        test_snapshots = [s for s in data if s['id'] == self.snapshot.id]
        self.assertEqual(len(test_snapshots), 1)
        self.assertEqual(float(test_snapshots[0]['total_value']), 100000.00)

    def test_snapshot_create(self):
        """Test snapshot creation endpoint."""
        data = {
            'portfolio': self.portfolio.id,
            'total_value': '120000.00',
            'snapshot_date': date.today().isoformat(),
            'calculated_from': 'all_accounts'
        }
        response = self.client.post('/api/v1/portfolio-snapshots/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['total_value']), 120000.00)

    def test_snapshot_retrieve(self):
        """Test snapshot detail endpoint."""
        response = self.client.get(f'/api/v1/portfolio-snapshots/{self.snapshot.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_value']), 100000.00)

    def test_snapshot_compare_to_previous(self):
        """Test snapshot comparison action."""
        # Create previous snapshot
        previous_date = date.today() - timedelta(days=1)
        previous = PortfolioSnapshot.objects.create(
            portfolio=self.portfolio,
            total_value=Decimal('90000.00'),
            snapshot_date=previous_date
        )

        response = self.client.get(
            f'/api/v1/portfolio-snapshots/{self.snapshot.id}/compare_to_previous/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['current']['value']), 100000.00)
        self.assertEqual(float(response.data['previous']['value']), 90000.00)
        self.assertEqual(float(response.data['difference']), 10000.00)

    def test_snapshot_compare_no_previous(self):
        """Test snapshot comparison when no previous exists."""
        # Create new portfolio with new snapshot
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        portfolio2 = Portfolio.objects.create(user=user2)
        snapshot2 = PortfolioSnapshot.objects.create(
            portfolio=portfolio2,
            total_value=Decimal('100000.00'),
            snapshot_date=date.today()
        )

        self.client.force_authenticate(user=user2)
        response = self.client.get(
            f'/api/v1/portfolio-snapshots/{snapshot2.id}/compare_to_previous/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class APIAuthenticationTestCase(TestCase):
    """Tests for API authentication and authorization."""

    def test_portfolio_requires_authentication(self):
        """Test portfolio endpoints require authentication."""
        client = APIClient()
        response = client.get('/api/v1/portfolios/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_account_requires_authentication(self):
        """Test account endpoints require authentication."""
        client = APIClient()
        response = client.get('/api/v1/accounts/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_history_requires_authentication(self):
        """Test history endpoints require authentication."""
        client = APIClient()
        response = client.get('/api/v1/account-history/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_snapshot_requires_authentication(self):
        """Test snapshot endpoints require authentication."""
        client = APIClient()
        response = client.get('/api/v1/portfolio-snapshots/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
