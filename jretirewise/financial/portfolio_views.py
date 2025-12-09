"""
Template views for portfolio management.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import date

from .models import Portfolio, Account, AccountValueHistory
from .forms import PortfolioForm, AccountForm, AccountValueHistoryForm


class PortfolioListView(LoginRequiredMixin, ListView):
    """View for listing user's portfolios."""

    model = Portfolio
    template_name = 'jretirewise/portfolio_list.html'
    context_object_name = 'portfolios'
    login_url = 'account_login'

    def get_queryset(self):
        """Return portfolios for current user."""
        return Portfolio.objects.filter(user=self.request.user).prefetch_related('accounts')

    def get_context_data(self, **kwargs):
        """Add context for each portfolio."""
        context = super().get_context_data(**kwargs)
        for portfolio in context['portfolios']:
            portfolio.account_count = portfolio.accounts.filter(status='active').count()
            portfolio.total_value = float(sum(acc.current_value for acc in portfolio.accounts.all()))

            # Group accounts by type
            accounts_by_type = {}
            for account in portfolio.accounts.all():
                acc_type = account.get_account_type_display()
                if acc_type not in accounts_by_type:
                    accounts_by_type[acc_type] = {'count': 0, 'total_value': 0}
                accounts_by_type[acc_type]['count'] += 1
                accounts_by_type[acc_type]['total_value'] += float(account.current_value)

            # Calculate percentage of portfolio for each account type
            if portfolio.total_value > 0:
                for acc_type in accounts_by_type:
                    accounts_by_type[acc_type]['percentage'] = round(
                        (accounts_by_type[acc_type]['total_value'] / portfolio.total_value) * 100, 1
                    )
            else:
                for acc_type in accounts_by_type:
                    accounts_by_type[acc_type]['percentage'] = 0

            portfolio.accounts_by_type = accounts_by_type

        return context


class PortfolioDetailView(LoginRequiredMixin, DetailView):
    """View for displaying portfolio details."""

    model = Portfolio
    template_name = 'jretirewise/portfolio_detail.html'
    context_object_name = 'portfolio'
    login_url = 'account_login'

    def get_queryset(self):
        """Return portfolio for current user only."""
        return Portfolio.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add accounts and calculations to context."""
        context = super().get_context_data(**kwargs)
        portfolio = context['portfolio']

        # Get all accounts
        accounts = portfolio.accounts.all()
        context['accounts'] = accounts

        # Calculate totals
        portfolio.account_count = accounts.filter(status='active').count()
        portfolio.total_value = float(sum(acc.current_value for acc in accounts))

        # Group accounts by type
        accounts_by_type = {}
        for account in accounts:
            acc_type = account.get_account_type_display()
            if acc_type not in accounts_by_type:
                accounts_by_type[acc_type] = {'count': 0, 'total_value': 0}
            accounts_by_type[acc_type]['count'] += 1
            accounts_by_type[acc_type]['total_value'] += float(account.current_value)

        # Calculate percentage of portfolio for each account type
        if portfolio.total_value > 0:
            for acc_type in accounts_by_type:
                accounts_by_type[acc_type]['percentage'] = round(
                    (accounts_by_type[acc_type]['total_value'] / portfolio.total_value) * 100, 1
                )
        else:
            for acc_type in accounts_by_type:
                accounts_by_type[acc_type]['percentage'] = 0

        portfolio.accounts_by_type = accounts_by_type

        # Calculate weighted average growth rate
        if portfolio.total_value > 0:
            weighted_growth = 0
            for account in accounts:
                if account.current_value > 0:
                    weight = float(account.current_value) / portfolio.total_value
                    weighted_growth += float(account.default_growth_rate) * weight
            portfolio.weighted_growth_rate = round(weighted_growth, 2)
        else:
            portfolio.weighted_growth_rate = 0

        # Calculate estimated portfolio value at retirement (simple 10-year projection)
        if portfolio.total_value > 0 and portfolio.weighted_growth_rate > 0:
            years = 10
            retirement_value = portfolio.total_value * ((1 + portfolio.weighted_growth_rate / 100) ** years)
            portfolio.estimated_retirement_value = round(retirement_value, 2)
        else:
            portfolio.estimated_retirement_value = portfolio.total_value

        return context


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new portfolio."""

    model = Portfolio
    form_class = PortfolioForm
    template_name = 'jretirewise/portfolio_form.html'
    success_url = reverse_lazy('financial:portfolio-list')
    login_url = 'account_login'

    def form_valid(self, form):
        """Set the user to current user."""
        form.instance.user = self.request.user
        messages.success(self.request, f'Portfolio "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Portfolio'
        return context


class PortfolioUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating a portfolio."""

    model = Portfolio
    form_class = PortfolioForm
    template_name = 'jretirewise/portfolio_form.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return portfolio for current user only."""
        return Portfolio.objects.filter(user=self.request.user)

    def get_success_url(self):
        """Redirect to portfolio detail after update."""
        return reverse_lazy('financial:portfolio-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """Save and show success message."""
        messages.success(self.request, f'Portfolio "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Portfolio'
        context['portfolio'] = self.object
        return context


class PortfolioDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting a portfolio."""

    model = Portfolio
    success_url = reverse_lazy('financial:portfolio-list')
    login_url = 'account_login'

    def get_queryset(self):
        """Return portfolio for current user only."""
        return Portfolio.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Delete and show success message."""
        portfolio_name = self.get_object().name
        messages.success(request, f'Portfolio "{portfolio_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


class AccountDetailView(LoginRequiredMixin, DetailView):
    """View for displaying account details."""

    model = Account
    template_name = 'jretirewise/account_detail.html'
    context_object_name = 'account'
    login_url = 'account_login'

    def get_queryset(self):
        """Return account for current user's portfolio only."""
        return Account.objects.filter(portfolio__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add value history to context."""
        from datetime import timedelta

        context = super().get_context_data(**kwargs)
        account = context['account']

        # Get value history (newest first)
        value_history_list = list(account.value_history.all().order_by('-recorded_date')[:10])

        # Calculate change from previous record for each entry
        for i, history in enumerate(value_history_list):
            if i < len(value_history_list) - 1:
                # There's a previous entry (older entry since ordered by -recorded_date)
                previous_value = value_history_list[i + 1].value
                history.change_amount = history.value - previous_value
                history.change_amount_abs = abs(history.change_amount)
                history.change_percent = (history.change_amount / previous_value * 100) if previous_value != 0 else 0
            else:
                # No previous entry, can't calculate change
                history.change_amount = None
                history.change_amount_abs = None
                history.change_percent = None

        context['value_history'] = value_history_list

        # Calculate historical analysis metrics
        if len(value_history_list) > 1:
            # Get all history in chronological order
            all_history = list(account.value_history.all().order_by('recorded_date'))

            if len(all_history) > 1:
                first_value = float(all_history[0].value)
                last_value = float(all_history[-1].value)

                # Total growth amount
                first_to_last_change = last_value - first_value
                context['first_to_last_change'] = first_to_last_change

                # Period growth rate
                if first_value > 0:
                    period_growth_rate = ((last_value - first_value) / first_value) * 100
                    context['period_growth_rate'] = period_growth_rate
                else:
                    context['period_growth_rate'] = 0

                # Days elapsed
                days_elapsed = (all_history[-1].recorded_date - all_history[0].recorded_date).days
                context['days_elapsed'] = days_elapsed if days_elapsed > 0 else 1
            else:
                context['first_to_last_change'] = 0
                context['period_growth_rate'] = 0
                context['days_elapsed'] = 0

        return context


class AccountCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new account."""

    model = Account
    form_class = AccountForm
    template_name = 'jretirewise/account_form.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return accounts for current user's portfolio only."""
        return Account.objects.filter(portfolio__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add portfolio to context."""
        context = super().get_context_data(**kwargs)
        portfolio_id = self.kwargs.get('portfolio_id')
        context['portfolio'] = get_object_or_404(
            Portfolio.objects.filter(user=self.request.user),
            pk=portfolio_id
        )
        return context

    def form_valid(self, form):
        """Set portfolio and user, and set defaults for omitted fields."""
        portfolio_id = self.kwargs.get('portfolio_id')
        portfolio = get_object_or_404(
            Portfolio.objects.filter(user=self.request.user),
            pk=portfolio_id
        )
        form.instance.portfolio = portfolio

        # Set default values for required fields not in form
        # inflation_adjustment and expected_contribution_rate are now in form, so they'll be set from form data
        form.instance.investment_allocation = '{}'  # Empty JSON object
        form.instance.withdrawal_priority = 0
        form.instance.withdrawal_restrictions = ''
        form.instance.rmd_age = 72
        form.instance.rmd_percentage = 0.0
        form.instance.data_source = 'manual'

        messages.success(self.request, f'Account "{form.instance.account_name}" created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to portfolio detail after creation."""
        return reverse_lazy('financial:portfolio-detail', kwargs={'pk': self.object.portfolio.pk})


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an account."""

    model = Account
    form_class = AccountForm
    template_name = 'jretirewise/account_form.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return account for current user's portfolio only."""
        return Account.objects.filter(portfolio__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add portfolio to context."""
        context = super().get_context_data(**kwargs)
        context['portfolio'] = self.object.portfolio
        return context

    def form_valid(self, form):
        """Save and show success message."""
        messages.success(self.request, f'Account "{form.instance.account_name}" updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to account detail after update."""
        return reverse_lazy('financial:account-detail', kwargs={'pk': self.object.pk})


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting an account."""

    model = Account
    login_url = 'account_login'

    def get_queryset(self):
        """Return account for current user's portfolio only."""
        return Account.objects.filter(portfolio__user=self.request.user)

    def get_success_url(self):
        """Redirect to portfolio detail after deletion."""
        return reverse_lazy('financial:portfolio-detail', kwargs={'pk': self.object.portfolio.pk})

    def delete(self, request, *args, **kwargs):
        """Delete and show success message."""
        account_name = self.get_object().account_name
        portfolio_pk = self.get_object().portfolio.pk
        messages.success(request, f'Account "{account_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


class AccountRecordValueView(LoginRequiredMixin, CreateView):
    """View for recording account values."""

    model = AccountValueHistory
    form_class = AccountValueHistoryForm
    template_name = 'jretirewise/account_record_value.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return value histories for current user's accounts only."""
        return AccountValueHistory.objects.filter(account__portfolio__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add account and recent history to context."""
        context = super().get_context_data(**kwargs)
        account_id = self.kwargs.get('account_id')
        account = get_object_or_404(
            Account.objects.filter(portfolio__user=self.request.user),
            pk=account_id
        )
        context['account'] = account
        context['recent_history'] = account.value_history.all().order_by('-recorded_date')[:5]
        return context

    def form_valid(self, form):
        """Set account and update account current value."""
        account_id = self.kwargs.get('account_id')
        account = get_object_or_404(
            Account.objects.filter(portfolio__user=self.request.user),
            pk=account_id
        )
        form.instance.account = account
        form.instance.recorded_by = self.request.user

        # Update account's current value
        account.current_value = form.instance.value
        account.save()

        messages.success(self.request, f'Value recorded for {account.account_name}!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to account detail after recording."""
        account_id = self.kwargs.get('account_id')
        return reverse_lazy('financial:account-detail', kwargs={'pk': account_id})

    def get_initial(self):
        """Set default values for form."""
        return {
            'recorded_date': date.today(),
            'source': 'manual',
        }


class AccountValueHistoryUpdateView(LoginRequiredMixin, UpdateView):
    """View for editing an account value history record."""

    model = AccountValueHistory
    form_class = AccountValueHistoryForm
    template_name = 'jretirewise/account_record_value.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return value histories for current user's accounts only."""
        return AccountValueHistory.objects.filter(account__portfolio__user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add account to context."""
        context = super().get_context_data(**kwargs)
        history = self.get_object()
        context['account'] = history.account
        context['recent_history'] = history.account.value_history.all().order_by('-recorded_date')[:5]
        context['page_title'] = f'Edit Value Record - {history.account.account_name}'
        return context

    def form_valid(self, form):
        """Update the value history record and account current value."""
        history = form.save(commit=False)
        account = history.account

        # Update account's current value if value changed
        account.current_value = form.instance.value
        account.save()

        messages.success(self.request, f'Value updated for {account.account_name}!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to account detail after updating."""
        history = self.get_object()
        return reverse_lazy('financial:account-detail', kwargs={'pk': history.account.pk})


class AccountValueHistoryDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting an account value history record."""

    model = AccountValueHistory
    template_name = 'jretirewise/accountvaluehistory_confirm_delete.html'
    login_url = 'account_login'

    def get_queryset(self):
        """Return value histories for current user's accounts only."""
        return AccountValueHistory.objects.filter(account__portfolio__user=self.request.user)

    def get_success_url(self):
        """Redirect to account detail after deletion."""
        history = self.get_object()
        return reverse_lazy('financial:account-detail', kwargs={'pk': history.account.pk})

    def delete(self, request, *args, **kwargs):
        """Delete and show success message."""
        history = self.get_object()
        account_name = history.account.account_name
        messages.success(request, f'Value record deleted for {account_name}!')
        return super().delete(request, *args, **kwargs)
