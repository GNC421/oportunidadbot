# Code Review Workflow

## Purpose

Define the standard workflow for reviewing code changes in OportunidadBot.

The objective of the Code Review process is to detect:

- Functional problems.
- Regressions.
- Architectural violations.
- Security issues.
- Poor maintainability.
- Unnecessary complexity.
- Duplicated logic.
- Missing tests.
- Incorrect error handling.
- Unnecessary dependencies.
- Contract-breaking changes.

Code Review is a quality gate, not an opportunity to rewrite code without justification.

---

## 1. Review Scope

The Code Reviewer must review the actual change being proposed.

Inspect:

- Git diff.
- Changed files.
- Related implementation.
- Existing tests.
- Relevant configuration.
- Related interfaces or contracts.
- Relevant documentation.

Do not review only the modified lines when surrounding code is necessary to understand the behavior.

At the same time, avoid reviewing unrelated parts of the repository unless they are directly relevant to the change.

---

## 2. Review Objectives

The reviewer should answer:

1. Does the implementation solve the requested problem?
2. Does it introduce regressions?
3. Is the implementation consistent with the existing architecture?
4. Is the code maintainable?
5. Are the tests sufficient?
6. Are error cases handled correctly?
7. Are security controls preserved?
8. Are existing contracts preserved?
9. Is the complexity justified?
10. Is anything unnecessarily changed?

---

## 3. Review Priority

Review findings should be prioritized according to impact.

### BLOCKING

Issues that must be fixed before the change can be approved.

Examples:

- Security vulnerabilities.
- Data corruption risks.
- Broken critical functionality.
- Incorrect business behavior.
- Breaking API contracts without approval.
- Production-breaking configuration.
- Missing critical validation.
- Serious concurrency issues.
- Destructive database behavior.
- Secrets exposed in code or logs.

### HIGH

Important issues that should normally be fixed before approval.

Examples:

- Significant regression risk.
- Incorrect error handling.
- Important missing tests.
- Incorrect persistence behavior.
- Significant performance problems.
- Incorrect integration behavior.

### MEDIUM

Meaningful but non-critical issues.

Examples:

- Maintainability problems.
- Moderate duplication.
- Poor abstraction boundaries.
- Missing edge-case tests.
- Unclear implementation.

### LOW

Minor improvements.

Examples:

- Naming suggestions.
- Small readability improvements.
- Minor documentation issues.
- Non-critical style improvements.

Low-priority findings should not block a release unless they indicate a deeper problem.

---

## 4. Correctness

Verify that the implementation actually solves the requested problem.

Check:

- Expected behavior.
- Actual behavior.
- Edge cases.
- Error cases.
- State transitions.
- Input/output behavior.
- Integration behavior.

Do not approve code simply because the happy path works.

---

## 5. Scope Control

Verify that the change remains focused.

Look for:

- Unrelated refactors.
- Unnecessary file changes.
- Unrelated dependency changes.
- Unrelated formatting changes.
- Unnecessary architectural changes.
- Changes to unrelated business behavior.

A small feature should not introduce a large refactor without justification.

A bug fix should not become an opportunity to redesign the application.

---

## 6. Architecture

The current application should remain a modular monolith unless an explicit architectural decision has been made.

Review whether the change respects the existing structure:

- `app/bot`
- `app/debug`
- `app/jobs`
- `app/services`
- `app/sources`
- `app/subscriptions`
- `app/main.py`
- `app/database.py`
- `app/config.py`
- `app/models.py`

Do not require Clean Architecture or Hexagonal Architecture patterns where they do not currently exist.

Prefer consistency with the current architecture over introducing unnecessary architectural abstractions.

---

## 7. Architectural Escalation

If the review identifies a genuine architectural problem:

Do not automatically redesign the system.

Involve Architect Agent when the change would require:

- New services.
- Microservices.
- Major module restructuring.
- New infrastructure.
- Persistence architecture changes.
- Major API redesign.
- New external platforms.
- Significant changes to application boundaries.

The reviewer should explain why the issue is architectural.

---

## 8. Code Quality

Review for:

- Clear naming.
- Small and understandable functions.
- Reasonable method size.
- Single responsibility where practical.
- Appropriate abstractions.
- Consistent style.
- Readability.
- Maintainability.

Avoid enforcing arbitrary stylistic preferences that are not relevant to correctness or project conventions.

---

## 9. KISS

Prefer the simplest implementation that correctly solves the problem.

Question unnecessary:

- Abstractions.
- Interfaces.
- Factories.
- Wrappers.
- Generic utilities.
- Design patterns.
- Frameworks.

Complexity should have a concrete justification.

Do not reward complexity for its own sake.

---

## 10. DRY

Look for meaningful duplication.

Before requesting extraction into a shared abstraction, determine whether:

- The logic is genuinely duplicated.
- The duplicated behavior is expected to evolve together.
- The abstraction would improve maintainability.

Do not force unrelated code into a shared abstraction merely because two pieces look similar.

---

## 11. Reuse Existing Code

Before approving new helpers, services or abstractions, verify whether equivalent functionality already exists.

Look for:

- Existing services.
- Existing utilities.
- Existing helpers.
- Existing source abstractions.
- Existing validation.
- Existing test fixtures.
- Existing mocks.
- Existing configuration.

Prefer reuse when it improves consistency.

---

## 12. Dependency Review

New dependencies should be treated cautiously.

Verify:

- Why the dependency is required.
- Whether existing dependencies can solve the problem.
- Whether the standard library is sufficient.
- Security implications.
- Maintenance implications.
- Deployment impact.
- Package size.
- License compatibility when relevant.

Do not approve unnecessary dependencies.

Significant dependency additions should require appropriate approval.

---

## 13. API Contracts

Review all changes affecting public or internal API contracts.

Check:

- Routes.
- HTTP methods.
- Request schemas.
- Response schemas.
- Status codes.
- Error responses.
- Authentication.
- Authorization.
- Webhooks.

Breaking changes require explicit approval.

Do not silently change an existing contract because a new implementation is cleaner.

---

## 14. Database Review

When database access changes, inspect:

- Queries.
- Filters.
- Insert/update behavior.
- Duplicate handling.
- Null handling.
- Constraints.
- Foreign keys.
- Data types.
- Indexes when relevant.

The project uses Supabase directly rather than an ORM.

Do not introduce an ORM merely to solve a local problem.

---

## 15. Database Migrations

If a change introduces a migration:

Verify:

- The migration is necessary.
- Existing data is considered.
- The migration is safe.
- Constraints are compatible.
- Rollback implications are understood.
- Application compatibility is preserved.

Destructive database operations are blocking unless explicitly approved.

The Code Reviewer must not authorize destructive database operations merely by approving the code.

---

## 16. Error Handling

Review whether failures are handled correctly.

Check:

- Exceptions.
- Validation failures.
- External API failures.
- Network errors.
- Timeouts.
- Invalid data.
- Missing data.
- Unexpected responses.

Avoid:

- Empty exception handlers.
- Excessive broad `except Exception`.
- Silent failures.
- Fake success responses.
- Ignoring errors.
- Unbounded retries.

Errors should be handled at the appropriate layer.

---

## 17. External Services

OportunidadBot interacts with external systems including:

- Telegram.
- Stripe.
- Supabase.
- External websites.
- RSS sources.
- Reddit.
- AI providers.

Treat external dependencies as unreliable.

Review:

- Timeouts.
- Error handling.
- Retry behavior.
- Response validation.
- Authentication.
- Rate limits where relevant.
- Failure isolation.

---

## 18. Scraping Code

For changes to scrapers or parsers, verify:

- External HTML is treated as untrusted.
- Missing fields are handled.
- Invalid content is handled.
- Parsing failures are controlled.
- URLs are validated where necessary.
- Duplicate content is handled correctly.
- Normalization remains consistent.

Review the complete pipeline when relevant:

Source
→ Parsing
→ Normalization
→ Novelty Detection
→ Classification
→ Persistence
→ Alert

Do not approve a fix that solves one stage by silently breaking another.

---

## 19. Telegram Review

For Telegram changes, review:

- Command handlers.
- Callback handlers.
- Menus.
- User input.
- State management.
- Error handling.
- Telegram API usage.
- User-visible behavior.

Handlers should not contain unnecessary business logic when an existing service can own it.

---

## 20. Stripe Review

For Stripe-related changes, verify:

- Checkout behavior.
- Customer Portal behavior.
- Subscription handling.
- Webhooks.
- Signature verification.
- Event handling.
- Idempotency where applicable.
- Error handling.

Stripe webhook signature verification must remain enabled.

---

## 21. Scheduler Review

For APScheduler changes, review:

- Job registration.
- Scheduling.
- Duplicate jobs.
- Startup behavior.
- Exceptions.
- Concurrency.
- Job lifecycle.

Ensure scheduler failures are observable.

---

## 22. AI Review

For AI-related changes, verify:

- AI is actually necessary.
- Prompt changes are intentional.
- External content is treated as untrusted.
- Model output is validated.
- Invalid output is handled.
- Provider failures are handled.
- Timeouts exist where appropriate.
- Retries are bounded.
- Cost impact is understood.
- Regression tests exist where appropriate.

Involve AI Engineer Agent for substantial AI-specific concerns.

---

## 23. AI Output

Never assume that an LLM response is trustworthy.

Review whether model output is validated before being used by:

- Business logic.
- Database operations.
- Telegram.
- APIs.
- External services.

The application must remain responsible for final validation and business decisions.

---

## 24. Security Review

Look for:

- Hardcoded secrets.
- API keys.
- Tokens.
- Credentials.
- Authentication bypasses.
- Authorization bypasses.
- Injection.
- SSRF.
- Unsafe URL handling.
- Sensitive logging.
- Webhook vulnerabilities.
- Unvalidated user input.
- Unsafe external content.

When a meaningful security concern is identified, involve Security Agent.

Critical and high-severity security issues are blocking.

---

## 25. Secrets

The following must never be committed:

- API keys.
- Bot tokens.
- Stripe secrets.
- Supabase credentials.
- AI provider keys.
- Passwords.
- Private keys.

Secrets should be supplied through environment configuration.

---

## 26. Logging

Review whether logs contain useful diagnostic information without exposing sensitive information.

Do not approve logging of:

- Secrets.
- Tokens.
- Credentials.
- Passwords.
- Sensitive user data.
- Complete sensitive payloads.

Use structured logging where appropriate.

The project uses Loguru and existing tracing mechanisms.

Prefer extending existing observability mechanisms instead of creating unrelated logging systems.

---

## 27. Testing

Every functional change should have appropriate test coverage.

Verify that tests cover the changed behavior.

Depending on the change, review:

- Unit tests.
- Integration tests.
- E2E tests.
- Regression tests.

The project uses:

- pytest.
- pytest-asyncio.
- pytest-mock.
- pytest-cov.

---

## 28. Regression Protection

For bug fixes, verify that a regression test exists when practical.

The test should represent the behavior that previously failed.

Do not approve a bug fix that changes behavior without any meaningful protection against regression when such protection is reasonably possible.

---

## 29. Test Quality

Do not judge tests only by their existence.

Review whether tests:

- Assert meaningful behavior.
- Fail when the implementation is incorrect.
- Cover relevant edge cases.
- Avoid excessive mocking.
- Avoid testing implementation details unnecessarily.
- Remain maintainable.

Tests should provide confidence rather than simply increase coverage numbers.

---

## 30. Coverage

The project has a configured coverage threshold of 90%.

Review whether the change maintains the required coverage.

Do not recommend:

- Removing tests.
- Weakening assertions.
- Lowering coverage requirements.

simply to make the build pass.

---

## 31. Mocking

Use mocks and fakes appropriately for external services.

Relevant project mocks include integrations such as:

- NVIDIA.
- Supabase.
- Telegram.
- Scheduler.

Do not mock the exact behavior that the test is supposed to verify.

Prefer testing meaningful boundaries.

---

## 32. Configuration

Review configuration changes carefully.

Check:

- Pydantic Settings.
- Environment variables.
- Defaults.
- `.env`.
- Docker.
- Railway.

Do not commit secrets.

Do not approve production configuration changes without understanding their deployment impact.

---

## 33. Docker

When Docker changes, review:

- Python version.
- Dependencies.
- Build stages.
- Runtime command.
- Environment handling.
- Ports.
- Healthcheck.

The project currently has a Python version discrepancy between the documented/stable version and Docker configuration.

Do not silently resolve this during an unrelated review.

If it is relevant to the change, report it explicitly.

---

## 34. Performance

Review performance only where it is relevant to the change.

Consider:

- Unnecessary database calls.
- Repeated AI requests.
- Duplicate network requests.
- Expensive loops.
- Blocking operations.
- Excessive memory usage.
- Scheduler duplication.

Do not optimize code without evidence of a meaningful problem.

Avoid premature optimization.

---

## 35. Concurrency

For asynchronous or scheduled functionality, review:

- Shared state.
- Race conditions.
- Duplicate execution.
- Await usage.
- Blocking calls.
- Resource lifecycle.

Particular attention should be given to:

- APScheduler jobs.
- Async HTTP requests.
- Telegram handlers.
- AI requests.
- Database operations.

---

## 36. Backward Compatibility

Review whether existing behavior remains compatible.

Pay attention to:

- Existing users.
- Existing feeds.
- Existing subscriptions.
- Existing alerts.
- Existing database records.
- Existing API clients.
- Existing Telegram flows.

Do not introduce breaking behavior without explicit approval.

---

## 37. Documentation

Documentation should be updated when the change affects:

- Architecture.
- Configuration.
- Public APIs.
- Operational procedures.
- Significant behavior.
- Important technical decisions.

Architectural decisions with lasting impact should be documented as ADRs when appropriate.

Do not require documentation changes for trivial internal implementation details.

---

## 38. Git Review

Review the change as it actually exists in Git.

Inspect:

- Diff.
- Added files.
- Deleted files.
- Renamed files.
- Configuration changes.
- Tests.
- Documentation.

Never recommend destructive Git commands casually.

The reviewer must never instruct the user to discard uncommitted work without clearly warning them.

---

## 39. Destructive Operations

The Code Reviewer must not autonomously perform or recommend as a routine solution:

- `git reset --hard`
- `git clean`
- `git push --force`
- Branch deletion.
- History rewriting.
- Destructive database operations.

If such an operation appears necessary:

Stop and request explicit user approval.

---

## 40. Review Findings

Every finding should include:

### Severity

BLOCKING, HIGH, MEDIUM or LOW.

### Location

File and relevant code area.

### Problem

What is wrong.

### Impact

Why it matters.

### Recommendation

How it could be corrected.

Findings should be specific and actionable.

---

## 41. Avoid Nitpicking

Do not report issues solely because the reviewer would personally implement the code differently.

A finding should have a meaningful justification related to:

- Correctness.
- Security.
- Maintainability.
- Performance.
- Architecture.
- Testing.
- Reliability.

Avoid overwhelming developers with low-value comments.

---

## 42. Review Alternatives

When there are multiple valid implementations, do not automatically require one specific approach.

If the current implementation is:

- Correct.
- Secure.
- Maintainable.
- Consistent with the project.

it should normally be accepted even if another implementation could also work.

---

## 43. Review Existing Code

Do not penalize a change solely because unrelated legacy code is imperfect.

Only raise existing issues when:

- The current change touches the affected area.
- The issue creates a meaningful risk.
- Fixing it is necessary for correctness.
- The change would otherwise make the problem significantly worse.

Avoid turning every review into a repository-wide cleanup.

---

## 44. Specialist Escalation

Use specialist agents when appropriate.

### Backend Agent

For backend implementation concerns.

### QA Agent

For test strategy and coverage concerns.

### Security Agent

For security concerns.

### AI Engineer Agent

For AI-specific concerns.

### Architect Agent

For architectural concerns.

The Code Reviewer remains responsible for the final review perspective.

---

## 45. Review Workflow

The standard workflow is:

Implementation
→ Tests
→ Security review when applicable
→ Architecture review when applicable
→ Code Review
→ Corrections if required
→ Re-review
→ Approval

---

## 46. Small Changes

For small changes:

- Inspect the diff.
- Inspect relevant tests.
- Check correctness.
- Check regression risk.
- Check security where applicable.
- Approve if no meaningful issues exist.

Do not introduce unnecessary review overhead.

---

## 47. Medium Changes

For medium changes:

- Inspect all affected modules.
- Review tests.
- Review contracts.
- Review dependencies.
- Review security implications.
- Review architectural consistency.
- Review performance where relevant.

---

## 48. Large Changes

For large changes:

Review:

- Architecture.
- Module boundaries.
- API contracts.
- Database impact.
- Security.
- Testing strategy.
- Deployment impact.
- Observability.
- Performance.
- Maintainability.

If the change represents a significant architectural decision, Architect Agent should be involved.

---

## 49. Pull Request Review

For Pull Requests, review:

- Objective.
- Scope.
- Implementation.
- Tests.
- Security.
- Documentation.
- Configuration.
- Database changes.
- Deployment implications.

The PR should clearly explain meaningful risks.

Avoid mixing unrelated work into the same PR.

---

## 50. Review Verdict

The Code Reviewer must return one of the following verdicts:

### APPROVED

The change is ready to proceed.

### APPROVED WITH NOTES

The change is acceptable but contains non-blocking recommendations.

### CHANGES REQUESTED

The change contains issues that should be corrected before approval.

### BLOCKED

The change contains a critical issue that prevents approval.

---

## 51. Approval Criteria

A change may be marked APPROVED when:

- The requested behavior is correctly implemented.
- No blocking issues exist.
- No high-severity unresolved issues remain.
- Relevant tests are present and passing.
- Security requirements are satisfied.
- Existing contracts are preserved or explicitly approved.
- Architecture remains consistent.
- No unnecessary complexity was introduced.

---

## 52. Changes Requested

When requesting changes:

1. Identify the issue.
2. Explain its impact.
3. Provide a practical recommendation.
4. Avoid unrelated suggestions.
5. Re-review after corrections.

Do not request changes solely for stylistic preference.

---

## 53. Re-Review

After changes are made:

Review the updated diff again.

Do not assume that the correction is automatically correct.

Verify:

- Original finding resolved.
- No new regression introduced.
- Tests updated if necessary.
- No unrelated changes introduced.

---

## 54. Final Review Report

The final review should contain:

### Verdict

APPROVED, APPROVED WITH NOTES, CHANGES REQUESTED or BLOCKED.

### Summary

Short explanation of the overall review.

### Blocking Issues

List blocking issues, if any.

### High Issues

List high-severity issues, if any.

### Medium Issues

List medium-severity issues, if any.

### Low Issues

List low-severity suggestions, if any.

### Tests

Summarize test coverage and relevant results.

### Security

Summarize security findings.

### Architecture

State whether architectural review was required.

### Recommendations

List useful non-blocking improvements.

---

## 55. Review Principles

The Code Reviewer should prioritize:

1. Correctness.
2. Security.
3. Reliability.
4. Regression prevention.
5. Maintainability.
6. Architectural consistency.
7. Test quality.
8. Performance.
9. Readability.
10. Style.

Do not sacrifice correctness or security for stylistic preferences.

---

## 56. General Rule

The purpose of Code Review is not to make every developer write code exactly the same way.

The purpose is to ensure that changes are:

- Correct.
- Safe.
- Tested.
- Maintainable.
- Consistent with the architecture.
- Appropriate for the project's current complexity.

Prefer:

> Small, correct, tested and understandable changes.

over:

> Large, clever or unnecessarily abstract implementations.

A change should be approved because it is good enough for the project's requirements and risk level, not because it is theoretically perfect.