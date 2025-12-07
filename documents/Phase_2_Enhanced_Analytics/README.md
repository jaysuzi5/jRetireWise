# Phase 2: Enhanced Analytics & Sophisticated Calculations

**Status**: Planned for implementation after Phase 1 MVP completion

**Estimated Duration**: 6-8 weeks

**Goals**:
- Build comprehensive multi-account portfolio management system
- Implement dynamic withdrawal rate calculators (including bucket-based strategies)
- Add Monte Carlo simulations and historical analysis
- Advanced visualization and scenario comparison

## Key Improvements Over Phase 1

### Foundation: Advanced Portfolio Management (2.0)

Phase 2 begins with a major upgrade to the portfolio system:

- **Multi-Account Support**: Manage 10+ account types (401k, IRA, taxable, HSA, etc.)
- **Flexible Growth Rates**: Each account has its own growth rate, overridable by scenarios
- **Value History Tracking**: Automatic snapshots of account values to track portfolio growth over time
- **Professional Portfolio Dashboard**: Visual breakdown, trend analysis, goal tracking

### New Calculation Engines

#### Dynamic Bucketed Withdrawal Rate Calculator
The most significant new calculation feature - allows retirement scenarios with changing withdrawal rates based on age/periods:

**Example Use Case**:
- Ages 55-59.5: 2% withdrawal (pre-retirement bridge)
- Ages 59.5-65: 4.5% withdrawal (early retirement, no Medicare)
- Ages 65-67: 3.5% withdrawal (Medicare available)
- Ages 67+: 2.5% withdrawal (Social Security available)

This is much more realistic than a single fixed withdrawal rate throughout retirement.

#### Enhanced Base Calculators
- 4% Rule: Reworked to support complex multi-account portfolios
- 4.7% Rule: Same enhancements as 4% rule
- Tax-aware withdrawal sequencing (which accounts to use in which order)

#### Additional Engines
- Monte Carlo: 1,000 to 100,000 scenario simulations
- Historical Period Analysis: Test against actual market returns since 1960s
- Sensitivity Analysis: What-if modeling for returns, spending, inflation

## Files in This Directory

- **plan.md** - Comprehensive Phase 2 detailed specification
  - 2.0 Advanced Portfolio Management (NEW)
  - 2.1 Advanced Calculation Engines (with Dynamic Bucketed Withdrawal)
  - 2.2 Asynchronous Processing (Celery/Redis)
  - 2.3 Monte Carlo, Historical, Sensitivity Calculators
  - 2.4 Advanced Visualization
  - 2.5 Scenario Comparison
  - 2.6 Frontend Enhancements
  - 2.7 Database Enhancements

- **README.md** (this file) - Quick reference and overview

## Implementation Sequence

### Phase 2.0: Advanced Portfolio (Priority 1)
Must be completed first as foundation for everything else:
1. Database schema for multi-account portfolios
2. Account CRUD API endpoints
3. Value history tracking system
4. Portfolio dashboard UI
5. Tests and documentation

### Phase 2.1: Enhanced Calculators (Priority 2)
Depends on 2.0, enables downstream testing:
1. Rework 4% and 4.7% rules for complex portfolios
2. Implement Dynamic Bucketed Withdrawal Rate calculator
3. Integration with portfolio system
4. API endpoints and validation
5. Frontend UI for bucket builder
6. Comprehensive testing

### Phase 2.2-2.7: Advanced Features (Priority 3+)
Can be developed in parallel with 2.1, but depend on 2.0:
- Async task processing (Celery/Redis)
- Monte Carlo, Historical, Sensitivity calculators
- Visualization components
- Scenario comparison
- Export/reporting features

## Key Design Decisions

### Portfolio as Foundation
Phase 2 is built around a professional portfolio management system. This is a major expansion from Phase 1's simple asset tracking.

**Impact**:
- All calculations now work with complex, multi-account portfolios
- Account types determine withdrawal rules and tax treatment
- Flexibility to model realistic retirement scenarios

### Dynamic Bucketed Withdrawal Rates
Rather than a single withdrawal rate, Phase 2 introduces "buckets" - periods where different withdrawal rates apply.

**Benefit**:
- Realistic retirement modeling (different needs at different ages)
- Account constraint modeling (401k available at 59.5, Medicare at 65, SS at 67)
- Healthcare cost adjustments
- Tax optimization opportunities

### Asynchronous Processing
Advanced calculations (Monte Carlo with 100k iterations) require async processing.

**Implementation**:
- Celery with Redis
- Progress tracking via polling or WebSocket
- Result caching for repeated scenarios

## Dependencies

### External Libraries
- **django-celery-beat**: Task scheduling
- **redis**: Broker for Celery
- **scipy**: Statistical functions for Monte Carlo
- **numpy**: Numerical computations
- **pandas**: Data manipulation for historical analysis

### Internal Dependencies
- Phase 1 MVP must be complete
- All Phase 1 tests passing
- Portfolio system (2.0) must be complete before 2.1 calculations

## Testing Strategy

### Unit Tests (70%)
- Account model validation
- Portfolio calculations
- History snapshot creation
- Bucket validation
- Withdrawal rate calculations
- Growth rate application

### Integration Tests (20%)
- Full calculation workflows
- Portfolio to calculator pipeline
- Database transactions
- API endpoint workflows
- Permission/authorization checks

### E2E Tests (10%)
- Create portfolio → add accounts → run calculation
- Bulk import → validate → calculate
- Scenario comparison UI workflow

## Documentation Requirements

1. **Code Documentation**
   - Model docstrings (Account, Portfolio, Bucket)
   - Calculator algorithm explanations
   - API endpoint examples

2. **User Documentation**
   - Portfolio setup guide
   - How to use bucket builder
   - Interpretation of results

3. **Developer Documentation**
   - Database schema diagrams
   - Calculation algorithm pseudocode
   - API specification

4. **CLAUDE.md Updates**
   - New Django management commands
   - New test suites to run
   - Deployment considerations (Redis for Celery)

## Success Criteria

- ✅ All Phase 1 tests still passing
- ✅ Portfolio system supports 10+ account types
- ✅ Automatic value history tracking working
- ✅ Dynamic Bucketed Withdrawal Rate calculator implemented
- ✅ 4% and 4.7% rules updated for complex portfolios
- ✅ Monte Carlo and historical analysis implemented
- ✅ Scenario comparison working
- ✅ All new tests passing (target 85%+ coverage)
- ✅ Full documentation
- ✅ Production deployment with Redis
- ✅ Performance acceptable (<10 sec for 100k iteration Monte Carlo)

## Questions & Clarifications Needed

Before implementation, confirm:
1. Account history: Monthly snapshots or user-triggered only?
2. Budget constraint: Can we add Redis dependency to Kubernetes?
3. Performance: Acceptable time for 100k Monte Carlo iterations?
4. UI: Should bucket timeline be drag-and-drop editable?
5. Export: PDF reports or just data export (CSV)?

## Related Documents

- See `../plan.md` for overall project roadmap
- See `../Phase_1_MVP/PHASE_1_COMPLETION_SUMMARY.md` for Phase 1 status
- See Phase 3 documentation for post-Phase 2 features
