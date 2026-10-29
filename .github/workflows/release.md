# Release Workflow

## Purpose

Define the standard workflow for preparing, validating and releasing changes in OportunidadBot.

The goal is to ensure that changes reaching production are:

- Tested.
- Reviewed.
- Secure.
- Compatible with the current infrastructure.
- Reproducible.
- Traceable.
- Safe to deploy.

This workflow applies to production releases and significant deployment changes.

---

# 1. Release Principle

A release should be the result of completed development work, not a separate opportunity to introduce additional functionality.

Do not add unrelated features, refactors or architectural changes during a release.

The release process should validate what has already been implemented.

---

# 2. Release Preconditions

Before preparing a release, verify:

- The requested functionality is complete.
- Relevant tests pass.
- No blocking Code Reviewer findings remain.
- Required Security review is complete.
- Required architectural decisions have been approved.
- Required documentation is updated.
- Required database migrations have been reviewed.
- Configuration changes are known.

Do not release a change that has unresolved blocking issues.

---

# 3. Release Scope

Identify exactly what is being released.

Review:

- Git diff.
- Commits included.
- Changed files.
- Configuration changes.
- Database changes.
- Docker changes.
- External integrations.
- API changes.
- AI changes.

Avoid releasing unrelated local changes.

---

# 4. Release Classification

Classify the release as:

## PATCH

Examples:

- Bug fix.
- Small validation change.
- Small internal correction.
- Documentation correction.

Requires normal test validation.

---

## MINOR

Examples:

- New functionality.
- New endpoint.
- New source.
- New Telegram functionality.
- New AI capability.
- New subscription functionality.

Requires full relevant testing and review.

---

## MAJOR

Examples:

- Breaking API changes.
- Major persistence changes.
- Major architectural changes.
- Significant deployment changes.
- Breaking behavior changes.

Requires explicit architectural analysis and user approval.

---

# 5. Pre-Release Agent Flow

For a normal release:

Implementation
    ↓
QA
    ↓
Security if applicable
    ↓
Code Reviewer
    ↓
Release validation
    ↓
Deploy

For major releases:

Architect
    ↓
User approval
    ↓
Implementation
    ↓
QA
    ↓
Security
    ↓
Code Reviewer
    ↓
Release validation
    ↓
Deploy

---

# 6. QA Release Validation

QA should verify:

- Full relevant test suite.
- Regression tests.
- Integration tests.
- E2E tests where applicable.
- Coverage threshold.
- Critical application flows.

The configured project coverage threshold should be respected.

Do not remove or weaken tests to satisfy release requirements.

---

# 7. Full Test Suite

For significant releases, run the complete test suite.

At minimum, verify:

- Unit tests.
- Integration tests.
- E2E tests.

If the complete suite cannot be executed, clearly document:

- Which tests were executed.
- Which tests were not executed.
- Why they could not be executed.
- Potential impact.

---

# 8. Security Release Validation

Security review is required when the release affects:

- Authentication.
- Authorization.
- Webhooks.
- External URLs.
- User-controlled input.
- Secrets.
- Telegram.
- Stripe.
- Supabase.
- AI.
- Administrative endpoints.
- Network communication.

Verify that:

- No secrets are committed.
- Environment variables are correctly used.
- Sensitive information is not logged.
- Webhook validation remains active.
- Authentication remains active.
- Security controls were not accidentally removed.

Critical or high-severity security findings block the release.

---

# 9. Configuration Validation

Review configuration changes carefully.

Check:

- Environment variables.
- `.env` usage.
- Production configuration.
- API keys.
- Telegram configuration.
- Stripe configuration.
- Supabase configuration.
- AI provider configuration.
- Logging configuration.

Never commit real production secrets.

Never expose secrets in release notes or logs.

---

# 10. Docker Validation

When Docker-related files change:

Review:

- Base Python version.
- Installed dependencies.
- Build process.
- Runtime command.
- Environment handling.
- Exposed ports.
- Healthcheck behavior.

The current project has a known Python version discrepancy:

- `requirements.txt` documentation indicates Python 3.12 as the stable version.
- Docker currently uses Python 3.11.

Do not resolve this discrepancy automatically during a release.

It should be treated as a separate explicit decision unless the current task requires resolving it.

---

# 11. Database Changes

If the release contains database changes:

Verify:

- Migration exists.
- Migration is reviewed.
- Existing data is preserved where required.
- New constraints are compatible.
- Indexes are appropriate.
- Rollback implications are understood.
- Application code is compatible with the new schema.

Database migrations require explicit approval before execution when they can modify existing production data or schema.

Never execute destructive production database operations autonomously.

---

# 12. API Compatibility

Before release, verify that existing API contracts remain compatible.

Pay particular attention to:

- HTTP methods.
- Routes.
- Request schemas.
- Response schemas.
- Authentication.
- Error responses.
- Webhooks.

Breaking API changes require explicit approval.

---

# 13. Telegram Compatibility

For Telegram-related changes, verify:

- Bot startup.
- Commands.
- Menus.
- Handlers.
- Callback behavior.
- Error handling.
- Telegram secret validation where applicable.

Avoid changing existing user-visible behavior unintentionally.

---

# 14. Stripe Compatibility

For Stripe-related changes, verify:

- Checkout.
- Customer Portal.
- Webhooks.
- Event handling.
- Signature validation.
- Subscription state.
- Error handling.

Stripe webhook validation must remain enabled.

Do not log complete sensitive Stripe payloads unnecessarily.

---

# 15. AI Release Validation

For releases containing AI changes, verify:

- Correct model configuration.
- Prompt changes.
- Output validation.
- Error handling.
- Timeouts.
- Retry behavior.
- Cost impact.
- Latency impact.
- Prompt injection protections.
- Regression examples.

Do not enable a new AI provider or production model without the required approval.

---

# 16. External Sources

For changes affecting scrapers or external sources, verify:

- RSS parsing.
- Reddit integration.
- Tablón source.
- HTTP behavior.
- Timeouts.
- Error handling.
- Duplicate detection.
- Normalization.
- Novelty detection.

External services must be treated as unreliable dependencies.

The application should fail gracefully when an external source is unavailable.

---

# 17. Observability

Before release, verify that relevant functionality produces sufficient observability.

Check:

- Loguru logging.
- Structured logs.
- Error logs.
- Execution traces.
- Debug information.
- Metrics where applicable.

Logs must not contain:

- Secrets.
- Tokens.
- Credentials.
- Sensitive user information.

---

# 18. Healthcheck

Verify that the application healthcheck remains functional.

The healthcheck should provide a reliable indication that the application is running.

Do not use the healthcheck as proof that every external dependency is functioning correctly.

---

# 19. Railway Deployment

The production deployment currently uses Railway.

Before deploying:

- Verify the intended branch/commit.
- Verify required environment variables.
- Verify Docker configuration when applicable.
- Verify healthcheck behavior.
- Verify startup command.
- Verify required external services.

Do not modify Railway production configuration autonomously when the change has meaningful deployment impact.

---

# 20. Deployment

Deployment should be performed only after release validation succeeds.

Before deployment, confirm:

- Correct commit.
- Correct environment.
- Correct configuration.
- Tests passing.
- Review approved.

Do not force-push or rewrite Git history as part of deployment.

---

# 21. Post-Deployment Validation

After deployment, verify:

- Application starts.
- Healthcheck succeeds.
- API responds.
- Telegram bot is operational.
- Scheduled jobs start correctly.
- Database connectivity works.
- External sources can be accessed.
- AI integration works when applicable.
- Stripe integration works when applicable.
- Logs show no unexpected startup errors.

---

# 22. Smoke Tests

Perform a small production smoke test covering the affected functionality.

Examples:

### Backend

- Healthcheck.
- Relevant endpoint.
- Error response.

### Telegram

- Bot responds.
- Relevant command works.
- Relevant menu works.

### Scraping

- Source can be fetched.
- Items can be parsed.
- Novelty detection works.

### AI

- Classification works.
- Invalid output is handled.

### Stripe

- Webhook endpoint responds correctly.
- Signature validation remains active.

Only execute actions that are safe for the production environment.

---

# 23. Rollback

If a release causes a significant production problem:

1. Stop further changes.
2. Identify the failing component.
3. Determine whether rollback is safe.
4. Restore the previous known-good version when appropriate.
5. Verify service health.
6. Investigate the root cause.

Do not execute destructive rollback operations automatically.

Database rollback requires special consideration because application rollback and database rollback are not always symmetrical.

---

# 24. Release Failure

A release should be considered failed if:

- Application cannot start.
- Healthcheck fails.
- Critical functionality is unavailable.
- Data corruption occurs.
- Security controls are broken.
- Critical integrations fail.
- Severe regressions appear.

In such cases:

- Stop deployment progression.
- Document the problem.
- Roll back when appropriate.
- Create a bug-fix task.
- Add a regression test when possible.

---

# 25. Release Documentation

For significant releases, document:

- Release identifier.
- Main changes.
- Database changes.
- Configuration changes.
- Infrastructure changes.
- Tests executed.
- Security review.
- Deployment status.
- Known limitations.

Do not document secrets or sensitive configuration values.

---

# 26. Git Safety

The release workflow must never automatically execute:

- `git reset --hard`
- `git clean`
- `git push --force`
- Branch deletion.
- History rewriting.
- Commands that discard user changes.

If a destructive Git operation appears necessary:

Stop and ask the user.

---

# 27. Final Release Gate

Before considering a release complete:

- [ ] Implementation complete.
- [ ] Relevant tests pass.
- [ ] Full test suite executed when required.
- [ ] Coverage requirements satisfied.
- [ ] Security review completed when applicable.
- [ ] Architecture approved when applicable.
- [ ] Code Review approved.
- [ ] Database changes reviewed.
- [ ] Configuration reviewed.
- [ ] Docker reviewed when applicable.
- [ ] Production deployment completed.
- [ ] Healthcheck verified.
- [ ] Smoke tests completed.
- [ ] No critical production errors detected.

---

# 28. Final Release Report

The final response should contain:

## Release

Identify the released change.

## Changes

Summarize the relevant changes.

## Tests

List tests executed and their results.

## Security

State the security review status.

## Database

State whether database changes were included.

## Deployment

State the deployment status.

## Smoke Tests

List the production validations performed.

## Known Issues

List remaining non-blocking issues.

## Rollback

State whether rollback was required.

---

# 29. General Rule

A release is not complete simply because the code works locally.

The release process must establish:

> Code works → tests pass → security is acceptable → review is approved → deployment succeeds → production is verified.

Production safety has priority over deployment speed.