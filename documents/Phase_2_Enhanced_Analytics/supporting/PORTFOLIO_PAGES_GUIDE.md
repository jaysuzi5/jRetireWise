# Portfolio Management Pages - Visual Guide

## Page Navigation Map

```
┌─────────────────────────────────────────────────────────────┐
│                    Navigation Menu                          │
│ Dashboard | Portfolio | Profile | Scenarios                │
└─────────────────────────────────────────────────────────────┘
                           ↓
          ┌────────────────────────────────┐
          │  Portfolio List Page           │
          │  /financial/portfolios/        │
          │                                │
          │  • View all portfolios         │
          │  • See portfolio summaries     │
          │  • Create new portfolio        │
          └────────────────────────────────┘
                      ↓            ↓
            ┌──────────┴────┬──────┘
            ↓               ↓
    ┌───────────────┐  ┌──────────────────┐
    │ Portfolio     │  │ Create Portfolio │
    │ Detail Page   │  │ /portfolios/     │
    │               │  │ create/          │
    │ Shows:        │  │                  │
    │ • All accounts│  │ Form to create   │
    │ • Total value │  │ new portfolio    │
    │ • Account     │  │                  │
    │   types       │  │                  │
    │ • Buttons to  │  │                  │
    │   add/edit    │  └──────────────────┘
    │   accounts    │
    └───────────────┘
         ↓      ↓  ↓
    ┌────┴─┬────┴──┬───────────────┐
    ↓      ↓       ↓               ↓
 View    Edit   Delete        Add Account
Account  Account  Portfolio   /portfolios/<id>/
Detail   /edit/             accounts/create/
  |        |       |              |
  ↓        ↓       ↓              ↓
┌──────────────────────────────────────┐
│  Account Detail Page                 │
│  /financial/accounts/<id>/           │
│                                      │
│  Shows:                              │
│  • Account info                      │
│  • Current value                     │
│  • Growth rates                      │
│  • Tax treatment                     │
│  • Value history                     │
│  • Record value button               │
│  • Edit/Delete buttons               │
└──────────────────────────────────────┘
       ↓                      ↓
    Edit              Record Value
 Account Form      /accounts/<id>/
 /accounts/        record-value/
 <id>/edit/              |
                    ┌────┴─────┐
                    ↓          ↓
            Record Form    Value History
            Updates        (displayed on
            Account        Account Detail
            Value
```

---

## Page Details

### 1. Portfolio List Page
**URL**: `/financial/portfolios/`
**Purpose**: View all user portfolios

```
┌─────────────────────────────────────────────────────────────┐
│ Portfolio Management                                        │
│ Manage your investment portfolios and accounts             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Portfolio Card                                       │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │                                                      │ │
│  │ Test Portfolio              Total Value: $675,000   │ │
│  │ (Description if provided)                           │ │
│  │                                                      │ │
│  │ Active Accounts: 3 │ Created: Dec 7, 2025           │ │
│  │ Last Updated: Dec 7, 2025                           │ │
│  │                                                      │ │
│  │ Accounts by Type:                                    │ │
│  │ • Savings Account (1) - $25,000                     │ │
│  │ • Roth IRA (1) - $150,000                           │ │
│  │ • Taxable Brokerage (1) - $500,000                  │ │
│  │                                                      │ │
│  │                         [View Details] [Edit] [...]  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  (More portfolio cards...)                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Empty State (if no portfolios):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                         [Icon]                              │
│              No portfolios yet                              │
│  Start by creating your first portfolio to begin tracking  │
│              your investments.                              │
│                                                             │
│                  [Create Portfolio]                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Portfolio Detail Page
**URL**: `/financial/portfolios/{id}/`
**Purpose**: View portfolio with all accounts

```
┌─────────────────────────────────────────────────────────────┐
│ Test Portfolio                      [← Back to Portfolios]  │
│ (Description)                                               │
├─────────────────────────────────────────────────────────────┤
│ Total Value: $675,000  │ Active Accounts: 3                │
│ Created: Dec 7, 2025   │ Last Updated: Dec 7, 2025         │
├─────────────────────────────────────────────────────────────┤
│ Accounts                                 [+ Add Account]    │
├────────────┬──────────┬──────────┬──────┬──────┬────────────┤
│ Name       │ Type     │ Value    │ Rate │Stat  │ Actions    │
├────────────┼──────────┼──────────┼──────┼──────┼────────────┤
│Emergency   │Savings   │$25,000   │7.0%  │Active│View Edit   │
│Fund        │          │          │      │      │ Delete     │
├────────────┼──────────┼──────────┼──────┼──────┼────────────┤
│Roth IRA    │Retirement│$150,000  │7.0%  │Active│View Edit   │
│            │IRA       │          │      │      │ Delete     │
├────────────┼──────────┼──────────┼──────┼──────┼────────────┤
│Taxable     │Investment│$500,000  │7.0%  │Active│View Edit   │
│Brokerage   │          │          │      │      │ Delete     │
└────────────┴──────────┴──────────┴──────┴──────┴────────────┘

Accounts by Type Summary:
┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐
│ Savings Account │  │ Roth IRA     │  │ Taxable         │
│ 1 account       │  │ 1 account    │  │ Brokerage       │
│ $25,000         │  │ $150,000     │  │ 1 account       │
│                 │  │              │  │ $500,000        │
└─────────────────┘  └──────────────┘  └─────────────────┘
```

---

### 3. Account Detail Page
**URL**: `/financial/accounts/{id}/`
**Purpose**: View complete account information and history

```
┌─────────────────────────────────────────────────────────────┐
│ Emergency Fund                           [Edit] [Back]      │
│ Test Portfolio                                              │
├─────────────────────────────────────────────────────────────┤
│ Current Value: $25,000   │ Account Type: Savings Account    │
│ Growth Rate: 7.00%       │ Status: ✓ Active                │
├─────────────────────────────────────────────────────────────┤
│ Account Information          │ Financial Metrics             │
├──────────────────────────────┼──────────────────────────────┤
│ Institution: Bank Name       │ Current Value: $25,000       │
│ Account #: ****1234          │ Growth Rate: 7.00%           │
│ Tax Treatment: Pre-Tax       │ Inflation Adj: 0.00%         │
│ Data Source: Manual Entry    │ Annual Contribution: $0.00   │
│ Created: Dec 7, 2025         │                              │
│ Description: ...             │                              │
└──────────────────────────────┴──────────────────────────────┘

Value History                       [+ Record Value]
┌──────────┬───────────┬────────┬─────────┬──────────┐
│Date      │Value      │Change  │Source   │Notes     │
├──────────┼───────────┼────────┼─────────┼──────────┤
│Dec 7,2025│$27,000.00 │+$2,000 │Manual   │Updated   │
├──────────┼───────────┼────────┼─────────┼──────────┤
│Dec 7,2025│$25,000.00 │-      │Manual   │Initial   │
└──────────┴───────────┴────────┴─────────┴──────────┘

(No value history yet? Shows empty state with "Record Value" button)
```

---

### 4. Record Value Page
**URL**: `/financial/accounts/{id}/record-value/`
**Purpose**: Record new account value

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Emergency Fund                                    │
│                                                             │
│ Record Account Value                                        │
│ Emergency Fund (Savings Account)                            │
├─────────────────────────────────────────────────────────────┤
│ Current Value on Record: $25,000.00                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Account Value *                                             │
│ [_______________________]                                   │
│                                                             │
│ Date *                                                      │
│ [2025-12-07] (date picker)                                 │
│                                                             │
│ Source *                                                    │
│ [Manual ▼] (dropdown with: manual, statement, api)         │
│                                                             │
│ Notes                                                       │
│ [_______________________]                                   │
│ [_______________________]                                   │
│                                                             │
│                      [Cancel] [Record Value]                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Recent Recordings                                           │
│                                                             │
│ Dec 7, 2025  │  $25,000.00  │ Manual                       │
│ Dec 6, 2025  │  $24,500.00  │ Statement                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Account Create/Edit Page
**URL**: `/financial/accounts/create/` or `/financial/accounts/{id}/edit/`
**Purpose**: Create or modify account details

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Test Portfolio                                    │
│                                                             │
│ Add Account to Portfolio (or Edit Account)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Account Name *                                              │
│ [_______________________]                                   │
│                                                             │
│ Account Type *                                              │
│ [Select Type ▼]  (19 types available)                      │
│                                                             │
│ Institution Name                                            │
│ [_______________________]                                   │
│                                                             │
│ Account Number                                              │
│ [_______________________]                                   │
│                                                             │
│ Current Value *                                             │
│ [_______________________]                                   │
│                                                             │
│ Expected Growth Rate (Annual %)                             │
│ [7.0_____] (percent)                                        │
│                                                             │
│ Tax Treatment                                               │
│ [Select Treatment ▼]  (pre_tax, post_tax, tax_free)        │
│                                                             │
│ Status                                                      │
│ [Active ▼]  (active, closed, merged)                       │
│                                                             │
│ Description                                                 │
│ [_______________________]                                   │
│ [_______________________]                                   │
│                                                             │
│                      [Cancel] [Create/Update]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 6. Portfolio Create/Edit Page
**URL**: `/financial/portfolios/create/` or `/financial/portfolios/{id}/edit/`
**Purpose**: Create or modify portfolio

```
┌─────────────────────────────────────────────────────────────┐
│ ← Back to Portfolios                                        │
│                                                             │
│ Create New Portfolio (or Edit Portfolio)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Portfolio Name *                                            │
│ [_______________________]                                   │
│                                                             │
│ Description                                                 │
│ [_______________________]                                   │
│ [_______________________]                                   │
│ [_______________________]                                   │
│                                                             │
│                      [Cancel] [Create/Update]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Account Types Supported (19 Total)

### Retirement Accounts
- Traditional 401k
- Roth 401k
- Traditional IRA
- Roth IRA
- SEP IRA
- Solo 401k

### Investment Accounts
- Taxable Brokerage
- Joint Account
- Partnership

### Savings Accounts
- Savings
- High-Yield Savings
- Money Market

### Health Accounts
- HSA (Health Savings Account)
- MSA (Medical Savings Account)

### Other
- 529 Plan (Education)
- CD (Certificate of Deposit)
- Bonds
- Treasuries
- Custom

---

## Common Workflows

### Workflow 1: Create New Portfolio
1. Navigate to Portfolio menu → Click "Portfolio"
2. Click "Create Portfolio" button
3. Enter portfolio name (e.g., "Retirement Portfolio")
4. Optionally add description
5. Click "Create Portfolio"
6. You're taken to portfolio detail page

### Workflow 2: Add Account to Portfolio
1. Go to Portfolio Detail page
2. Click "+ Add Account" button
3. Fill in account details:
   - Account Name (required)
   - Account Type from dropdown (required)
   - Institution name (optional)
   - Current Value (required)
   - Growth rate, tax treatment, etc.
4. Click "Create Account"
5. Account appears in account list

### Workflow 3: Track Account Value Changes
1. Go to Account Detail page
2. Click "+ Record Value" button
3. Enter new account value
4. Select date and source
5. Add optional notes
6. Click "Record Value"
7. Value history updates automatically
8. Account's current value updates

### Workflow 4: View Portfolio Summary
1. Navigate to Portfolio List
2. See all portfolios with:
   - Total value
   - Account count
   - Accounts grouped by type
3. Click "View Details" to see all accounts

---

## Dark Mode Support

All pages automatically adapt to dark mode:
- Dark backgrounds (#111827, #1f2937)
- Light text colors
- Consistent color scheme
- Toggle via theme button in navigation

---

## Responsive Design

All pages are responsive and work on:
- Desktop (1920px+)
- Tablet (768px - 1024px)
- Mobile (320px - 767px)

---

## Form Validation

All forms include:
- Required field indicators (*)
- Client-side validation
- Server-side validation
- Clear error messages
- Focus management

---

## Notes

- All pages require authentication
- Users see only their own data
- Success/error messages appear after actions
- Navigation breadcrumbs help users find their way
- All forms are CSRF-protected
- Timestamps show when data was created/updated

