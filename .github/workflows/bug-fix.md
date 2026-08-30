# Bug Fix Workflow

## Purpose

Define the standard workflow for diagnosing, implementing, testing and reviewing bug fixes in OportunidadBot.

The primary objective is to identify and correct the root cause of a problem while minimizing the risk of introducing regressions.

Bug fixes must prioritize:

- Correctness.
- Root cause analysis.
- Minimal and focused changes.
- Regression prevention.
- Test coverage.
- Security.
- Maintainability.

---

## 1. Initial Bug Analysis

Before modifying code, understand the problem.

Determine:

- What is the expected behavior.
- What is the actual behavior.
- How the problem can be reproduced.
- Which component is affected.
- Which code path is involved.
- Whether the problem is deterministic or intermittent.
- Whether relevant logs or traces exist.
- Whether existing tests already cover the affected behavior.

Do not modify code before understanding the affected area unless the problem is obvious and the required change is trivial.

---

## 2. Reproduce the Bug

Whenever possible, reproduce the problem before implementing the fix.

Use:

- Existing tests.
- A new temporary reproduction.
- Relevant unit tests.
- Integration tests.
- E2E tests.
- Logs.
- Debug traces.

The reproduction should provide enough information to determine whether the observed behavior matches the reported bug.

If the bug cannot be reproduced, do not invent a root cause.

Instead:

1. Inspect the relevant implementation.
2. Inspect available logs.
3. Inspect related tests.
4. Identify plausible causes.
5. Clearly state any remaining uncertainty.

---

## 3. Identify the Root Cause

The goal is to fix the cause, not only the symptom.

Investigate:

- Input validation.
- Business logic.
- State management.
- Persistence.
- Database operations.
- External APIs.
- HTTP requests.
- Scraping.
- Parsing.
- Normalization.
- Novelty detection.
- AI classification.
- Scheduler behavior.
- Telegram interactions.
- Stripe interactions.
- Configuration.
- Error handling.
- Concurrency.
- Resource management.

Do not assume that the first suspicious line is necessarily the root cause.

---

## 4. Determine the Scope

Before implementing the fix, determine whether the issue is:

### Local

The problem is isolated to a single function, class or module.

Prefer a local fix.

### Cross-module

The problem affects multiple components.

Inspect the interactions between those components before modifying them.

### Architectural

The problem is caused by a fundamental architectural decision.

In this case, involve the Architect Agent.

Do not turn a local bug into an architectural refactor unless the architecture genuinely prevents a correct solution.

---

## 5. Regression Test

Whenever practical, create or update a regression test for the bug.

The regression test should:

1. Reproduce the incorrect behavior.
2. Fail before the fix.
3. Pass after the fix.
4. Protect against the bug returning in the future.

Prefer a focused regression test over broad changes to unrelated tests.

Do not remove or weaken an existing test simply because it conflicts with the new implementation.

---

## 6. Choose the Appropriate Agent

Use the specialist that owns the affected area.

### Backend Agent

Use for bugs involving:

- Python.
- FastAPI.
- Services.
- Database access.
- Supabase.
- Scheduler.
- Scrapers.
- HTTP integrations.
- Telegram backend logic.
- Stripe backend logic.

### AI Engineer Agent

Use for bugs involving:

- LLM classification.
- Prompts.
- Model configuration.
- AI provider integration.
- AI output parsing.
- AI output validation.
- Prompt injection.
- AI latency.
- AI cost.
- AI reliability.

### Security Agent

Use for bugs involving:

- Authentication.
- Authorization.
- Secrets.
- Token handling.
- SSRF.
- Injection.
- Webhooks.
- User-controlled URLs.
- Sensitive information.
- Administrative endpoints.
- Security controls.

### QA Agent

Use to determine:

- Regression coverage.
- Missing test cases.
- Integration coverage.
- E2E coverage.
- Edge cases.
- Validation strategy.

### Architect Agent

Use only when:

- The root cause is architectural.
- The fix requires changing module boundaries.
- The fix requires replacing infrastructure.
- The fix requires changing persistence architecture.
- The fix requires a significant API contract change.
- The fix requires a major architectural refactor.

### Code Reviewer Agent

Use as the final quality gate for meaningful bug fixes.

---

## 7. Implementation Principles

The fix should follow these principles:

- Make the smallest change that correctly solves the problem.
- Reuse existing functionality.
- Follow existing project conventions.
- Avoid unnecessary abstractions.
- Avoid unnecessary dependencies.
- Avoid unrelated refactoring.
- Preserve existing contracts.
- Preserve existing behavior outside the affected area.
- Keep error handling explicit.
- Keep functions and methods understandable.

Prefer:

> Minimal correct fix.

over:

> Large refactor that happens to fix the problem.

---

## 8. Do Not Hide the Problem

Do not fix a bug by hiding its symptoms.

Avoid solutions such as:

- Silencing exceptions without understanding them.
- Returning fake success responses.
- Removing failing assertions.
- Ignoring errors.
- Increasing timeouts without understanding the cause.
- Adding arbitrary retries.
- Adding broad exception handlers.
- Disabling validation.
- Suppressing logs that contain useful diagnostic information.

The system should fail safely and transparently when appropriate.

---

## 9. Error Handling

When fixing error-related behavior, verify:

- The correct exception is handled.
- Unexpected exceptions are not silently swallowed.
- Error messages are useful.
- Sensitive information is not exposed.
- Logs contain sufficient diagnostic information.
- External failures are handled appropriately.
- Retries are bounded when applicable.
- Timeouts are appropriate.

Do not use broad exception handling as a shortcut.

---

## 10. External Integrations

For bugs involving external services, consider:

- Network failures.
- Timeouts.
- Rate limits.
- Invalid responses.
- Empty responses.
- Unexpected response formats.
- Authentication failures.
- Service unavailability.
- Partial failures.

External services should be treated as unreliable dependencies.

The application should degrade gracefully whenever practical.

---

## 11. Scraping and Parsing Bugs

For bugs involving external sources:

Inspect the complete pipeline:

Source
→ Fetch
→ Parse
→ Normalize
→ Detect novelty
→ Classify
→ Persist
→ Alert

Determine exactly where the incorrect behavior occurs.

Do not modify downstream components if the root cause is upstream.

Consider:

- HTML structure changes.
- Missing fields.
- Invalid URLs.
- Encoding.
- Empty content.
- Duplicate items.
- Changed RSS formats.
- Unexpected Reddit content.
- Changed Tablón structure.
- Time/date formats.

Add regression fixtures when practical.

---

## 12. AI-Related Bugs

For AI-related bugs, involve AI Engineer Agent.

Inspect:

- Input provided to the model.
- Prompt.
- Model configuration.
- Output format.
- Output validation.
- Error handling.
- Retry behavior.
- Fallback behavior.
- Classification thresholds.
- Existing evaluation examples.

Consider whether the problem is actually caused by deterministic preprocessing rather than the LLM.

Do not modify prompts blindly.

When changing AI behavior, add regression examples whenever practical.

---

## 13. Database Bugs

For database-related bugs:

Inspect:

- Queries.
- Filters.
- Constraints.
- Data types.
- Existing records.
- Transaction behavior where applicable.
- Duplicate handling.
- Null handling.
- Foreign key relationships.
- Index usage when relevant.

Do not directly modify production data.

Do not perform destructive database operations autonomously.

Database schema changes require explicit approval.

---

## 14. Database Schema Changes

If fixing the bug requires:

- New columns.
- New tables.
- Constraints.
- Indexes.
- Data migrations.
- Schema changes.

Stop before applying the change if user approval is required.

Explain:

- Why the schema change is necessary.
- What will change.
- Impact on existing data.
- Migration strategy.
- Rollback implications.

Do not introduce a schema change merely because it is convenient.

---

## 15. Security Bugs

If the bug is security-related:

Prioritize security over convenience.

Immediately involve Security Agent.

Security analysis should consider:

- Attack vector.
- Exploitability.
- Impact.
- Authentication.
- Authorization.
- Input validation.
- Data exposure.
- Secrets.
- SSRF.
- Injection.
- Webhooks.
- External requests.
- Logging.

Critical and high-severity vulnerabilities are blocking issues.

Do not knowingly leave a critical security vulnerability unresolved while marking the bug as complete.

---

## 16. Telegram Bugs

For Telegram-related bugs, inspect:

- Command handlers.
- Callback handlers.
- Menus.
- State transitions.
- User input.
- Error handling.
- Bot lifecycle.
- Telegram API interactions.
- Webhook security where applicable.

Preserve existing user-visible behavior unless the bug requires changing it.

---

## 17. Stripe Bugs

For Stripe-related bugs, inspect:

- Checkout.
- Customer Portal.
- Subscription state.
- Webhooks.
- Event processing.
- Signature validation.
- Duplicate events.
- Error handling.

Stripe webhook signature validation must not be disabled to make a test or request succeed.

Consider webhook idempotency when relevant.

---

## 18. Scheduler Bugs

For APScheduler-related bugs, inspect:

- Job registration.
- Scheduling interval.
- Startup behavior.
- Duplicate jobs.
- Exceptions inside jobs.
- Concurrency.
- Job state.
- Interaction with the orchestrator.

Ensure that a scheduler failure does not silently corrupt the rest of the application.

---

## 19. Logging and Debugging

Use the existing observability mechanisms when diagnosing bugs.

Relevant mechanisms include:

- Loguru.
- Structured logging.
- Internal metrics.
- Debug traces.
- Debug dashboard.

Do not add permanent debug output unnecessarily.

Never log:

- API keys.
- Passwords.
- Tokens.
- Credentials.
- Secrets.
- Sensitive user information.

---

## 20. Configuration Bugs

When configuration is involved, inspect:

- Environment variables.
- Pydantic Settings.
- `.env`.
- Default values.
- Production configuration.
- Docker configuration.
- Railway configuration.

Do not commit real secrets.

Do not modify production configuration automatically.

---

## 21. Test Strategy

Every bug fix should have appropriate tests.

At minimum, consider:

### Unit tests

For isolated logic.

### Integration tests

For interactions between components.

### E2E tests

For complete critical flows.

Use the smallest appropriate testing level.

A simple isolated logic bug does not necessarily require a new E2E test.

A critical end-to-end regression may require more than a unit test.

---

## 22. Test Cases to Consider

Depending on the bug, consider:

- Happy path.
- Invalid input.
- Empty input.
- Missing values.
- Boundary values.
- Duplicate data.
- Unexpected external responses.
- Timeouts.
- Exceptions.
- Unauthorized access.
- Malformed data.
- Long content.
- Unicode content.
- Concurrent execution.
- Existing records.
- New records.

Only add meaningful cases.

Avoid creating tests solely to increase the number of tests.

---

## 23. Running Tests

After implementing the fix:

1. Run the regression test.
2. Run relevant unit tests.
3. Run relevant integration tests.
4. Run relevant E2E tests when applicable.
5. Run the complete suite when the change affects shared functionality.

The project currently uses:

- pytest.
- pytest-asyncio.
- pytest-mock.
- pytest-cov.

Respect the configured coverage threshold.

---

## 24. Existing Failing Tests

If tests were already failing before the bug fix:

Do not silently change them.

Determine whether the failure is:

- Related to the bug.
- Caused by the fix.
- Unrelated.
- Environmental.
- Caused by an external dependency.

Clearly report unrelated failures.

---

## 25. Never Delete Tests to Fix a Bug

Do not:

- Delete failing tests.
- Remove assertions.
- Reduce coverage requirements.
- Make tests less strict.
- Mock away the behavior being tested.

unless there is a documented and legitimate reason that the original test is no longer valid.

If expected behavior has intentionally changed, update the test to represent the new approved behavior.

---

## 26. Security Review

Security review should be performed when applicable.

Security Agent should verify that the fix does not introduce:

- New vulnerabilities.
- Secret exposure.
- Authentication bypass.
- Authorization bypass.
- SSRF.
- Injection.
- Data leakage.
- Unsafe external requests.

---

## 27. Code Review

After the fix and tests are complete, Code Reviewer should review the change.

The reviewer should verify:

- Root cause was correctly addressed.
- Fix is minimal.
- Regression test exists where appropriate.
- No unrelated code was changed.
- Existing behavior remains intact.
- Error handling is appropriate.
- Security concerns are addressed.
- Tests are meaningful.
- Architecture remains consistent.

---

## 28. Review Verdict

Code Reviewer should return one of:

### APPROVED

The fix is acceptable.

### APPROVED WITH NOTES

The fix is acceptable but contains non-blocking recommendations.

### CHANGES REQUESTED

The implementation requires corrections.

### BLOCKED

A critical problem prevents completion.

---

## 29. Changes Requested

If Code Reviewer requests changes:

1. Review each finding.
2. Determine the appropriate specialist.
3. Implement only the required corrections.
4. Run affected tests again.
5. Review the final diff.
6. Run Code Reviewer again.

Do not introduce unrelated improvements while addressing review findings.

---

## 30. Architectural Escalation

If investigation reveals that the bug cannot be safely fixed without a major architectural change:

Stop implementation.

Invoke Architect Agent.

The Architect should explain:

- Root architectural problem.
- Current limitation.
- Proposed solution.
- Alternatives.
- Risks.
- Migration impact.
- Testing impact.

Ask the user for approval when required.

Do not silently transform a bug fix into a major redesign.

---

## 31. Dependency Changes

If a dependency appears necessary to solve the bug:

Do not install it automatically when it has meaningful project impact.

Explain:

- Dependency.
- Problem it solves.
- Why existing libraries are insufficient.
- Security implications.
- Maintenance impact.
- Deployment impact.

Prefer existing dependencies or the standard library when sufficient.

---

## 32. Git Safety

Bug fixing must never automatically execute destructive Git operations.

Never autonomously execute:

- `git reset --hard`
- `git clean`
- `git push --force`
- Branch deletion.
- History rewriting.
- Commands that discard user changes.

If such an operation appears necessary:

Stop and ask the user.

---

## 33. Scope Control

Do not combine a bug fix with unrelated work.

For example, if fixing an RSS parser bug:

Do not automatically:

- Rewrite the complete source architecture.
- Replace `feedparser`.
- Introduce microservices.
- Refactor unrelated services.
- Rewrite unrelated tests.

Only broaden the scope when the broader change is necessary for a correct solution or explicitly requested.

---

## 34. Completion Criteria

A bug fix is complete only when:

- The bug is understood.
- Root cause is identified or clearly documented if uncertainty remains.
- The fix is implemented.
- Regression coverage exists when practical.
- Relevant tests pass.
- No new regressions are detected.
- Security concerns are addressed when applicable.
- Architectural approval was obtained when required.
- Code Review has no blocking findings.

---

## 35. Final Report

When the bug fix is complete, provide:

### Root Cause

Explain what caused the problem.

### Fix

Explain what was changed.

### Files Changed

List the relevant files.

### Tests

List the tests executed and their results.

### Regression

Identify the regression test added or updated.

### Security

State whether Security Agent reviewed the change and the result.

### Architecture

State whether Architect Agent was involved.

### Code Review

State the final review verdict.

### Remaining Issues

List any known non-blocking issues.

---

## 36. General Rule

The bug-fixing process should follow:

Understand
→ Reproduce
→ Identify root cause
→ Add regression test
→ Implement minimal fix
→ Test
→ Security review when applicable
→ Code review
→ Complete

The objective is not simply to make the error disappear.

The objective is to restore the correct behavior while reducing the probability that the same problem happens again.