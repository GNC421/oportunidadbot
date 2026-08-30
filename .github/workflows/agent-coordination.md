# Agent Coordination Workflow

## Purpose

Define how specialized agents collaborate in OportunidadBot.

This document does not define the responsibilities of individual agents.
Those responsibilities are defined in their respective `.agent.md` files.

This workflow defines:

- When agents should be invoked.
- Which agent has priority.
- How agents exchange information.
- When execution must stop.
- When user approval is required.
- How conflicts between agents are resolved.
- How the final implementation is validated.

---

# 1. Core Principle

Agents must collaborate sequentially when the task requires multiple areas of expertise.

Do not invoke every available agent for every task.

Use the minimum number of agents necessary to complete the task safely.

The objective is:

> Use specialized agents only when their expertise materially improves the result.

---

# 2. Agent Responsibilities

The project currently contains the following specialized agents:

- Architect
- Backend
- QA
- Security
- AI Engineer
- Code Reviewer

Each agent owns its area of expertise.

Agents must not silently take ownership of another agent's domain.

For example:

- Backend should not make architectural decisions.
- QA should not redesign production code.
- Security should not redesign business logic.
- Code Reviewer should not implement large features.
- AI Engineer should not redesign the whole application.
- Architect should not unnecessarily implement detailed code.

---

# 3. Default Flow

For a normal feature, the preferred flow is:

User request
    ↓
Task analysis
    ↓
Architect (if necessary)
    ↓
Implementation specialist
    ↓
QA
    ↓
Security (if applicable)
    ↓
Code Reviewer
    ↓
Completion

Not every task requires every step.

---

# 4. Small Tasks

For small and localized changes:

Task
    ↓
Relevant implementation agent
    ↓
Tests
    ↓
Code Reviewer if appropriate

Examples:

- Small bug fix.
- Minor validation.
- Small refactor.
- Small endpoint change.
- Test improvement.
- Documentation update.

Do not invoke Architect simply because a task changes more than one line.

---

# 5. Medium Tasks

For medium-sized features:

Task
    ↓
Architect analysis
    ↓
Implementation agent
    ↓
QA
    ↓
Security if applicable
    ↓
Code Reviewer

The Architect should only provide architectural guidance.

The implementation agent remains responsible for implementing the feature.

---

# 6. Large Tasks

For large changes:

Task
    ↓
Architect
    ↓
User approval if required
    ↓
Implementation specialist(s)
    ↓
QA
    ↓
Security
    ↓
Code Reviewer
    ↓
Final validation

Do not begin implementation of a major architectural change before obtaining required user approval.

---

# 7. Agent Selection

## Architect

Invoke when the task affects:

- Architecture.
- Module boundaries.
- Major dependencies.
- Infrastructure.
- Persistence architecture.
- API contracts.
- Deployment architecture.
- Major AI architecture.
- New applications.
- Distributed systems.

Do not invoke for trivial implementation decisions.

---

## Backend

Invoke when the task affects:

- Python.
- FastAPI.
- Backend services.
- Database access.
- Supabase.
- Telegram backend logic.
- Scheduler.
- Scrapers.
- External integrations.
- Backend configuration.

---

## QA

Invoke when the task introduces or modifies:

- Business logic.
- APIs.
- Services.
- Scrapers.
- Persistence.
- AI behavior.
- Integrations.
- Bug fixes.

QA should ensure the behavior is properly tested.

---

## Security

Invoke when the task affects:

- Authentication.
- Authorization.
- Secrets.
- External URLs.
- HTTP requests.
- Webhooks.
- Telegram security.
- Stripe security.
- User-controlled content.
- AI security.
- Sensitive data.
- Administrative endpoints.

---

## AI Engineer

Invoke when the task affects:

- LLMs.
- Prompts.
- AI classification.
- AI providers.
- Model configuration.
- AI output validation.
- AI evaluation.
- AI cost.
- AI latency.
- Prompt injection.

---

## Code Reviewer

Invoke as the final quality gate for meaningful code changes.

Code Reviewer should review the implementation after the other specialists have completed their work.

---

# 8. Agent Communication

Agents should communicate through explicit written context.

When handing work from one agent to another, provide:

## Task

What needs to be achieved.

## Context

Relevant existing implementation and constraints.

## Changes

What has already been changed.

## Decisions

Important decisions already made.

## Risks

Known risks or concerns.

## Tests

Tests already executed.

## Open questions

Anything that still requires a decision.

Agents must not assume that another agent has made a decision unless it is explicitly documented.

---

# 9. Do Not Repeat Analysis

Before performing work, an agent should inspect the work already performed.

Do not repeat:

- Architecture analysis.
- Code investigation.
- Test creation.
- Security analysis.

unless new information requires it.

If another agent has already analyzed an area, reuse that analysis.

---

# 10. Architect Has Architectural Authority

Architect is responsible for architectural recommendations.

However, Architect does not have authority to approve major architectural changes autonomously.

If user approval is required:

Stop.

Explain:

- Current architecture.
- Proposed change.
- Reason.
- Alternatives.
- Risks.
- Recommendation.

Wait for the user.

---

# 11. Implementation Authority

Backend and AI Engineer can implement changes within their domain.

They must not independently:

- Introduce microservices.
- Replace infrastructure.
- Replace databases.
- Change major contracts.
- Introduce major frameworks.
- Change deployment architecture.

These decisions require Architect analysis and, when applicable, user approval.

---

# 12. QA Independence

QA should not simply confirm that the implementation works.

QA must attempt to identify:

- Missing edge cases.
- Regressions.
- Invalid inputs.
- Error paths.
- Integration problems.
- Incorrect assumptions.
- Insufficient test coverage.

QA can request implementation changes.

---

# 13. Security Independence

Security should independently evaluate security-sensitive changes.

Do not treat:

> "The feature works"

as evidence that:

> "The feature is secure."

Security findings should be classified by severity.

Critical and high-severity findings block completion.

---

# 14. Code Reviewer Independence

Code Reviewer should not automatically trust previous agents.

The reviewer must independently inspect:

- Diff.
- Implementation.
- Tests.
- Architecture.
- Security considerations.

The reviewer is the final quality gate.

---

# 15. Conflict Resolution

Agents may disagree.

When disagreement occurs:

## Technical disagreement

Prefer:

1. Existing project conventions.
2. Simpler implementation.
3. Existing abstractions.
4. Lower maintenance cost.
5. Lower risk.

---

## Architectural disagreement

Architect should provide the architectural recommendation.

If the decision is significant:

Ask the user.

---

## Security disagreement

Security concerns take priority when they identify a real vulnerability.

A feature should not bypass a security control simply for convenience.

---

## QA disagreement

If QA identifies a reproducible correctness or regression problem, the implementation should be corrected before approval.

---

## Code Review disagreement

Code Review findings must be evaluated.

If the finding is valid, fix it.

If the finding is intentionally rejected, document why.

---

# 16. User Approval Gates

The workflow must stop and request user approval before:

- Major architecture changes.
- Database migrations.
- Destructive database operations.
- New external infrastructure.
- New production dependencies with significant impact.
- API contract changes.
- Authentication changes.
- Authorization model changes.
- Deployment changes.
- Docker changes that affect production behavior.
- Changes to secrets or production configuration.
- Destructive Git operations.

---

# 17. Safe Autonomous Actions

Agents may generally perform:

- Reading files.
- Searching the repository.
- Creating code.
- Modifying code.
- Creating tests.
- Running tests.
- Running safe local commands.
- Updating documentation.
- Creating non-destructive helper scripts.

Actions must still remain within the current task scope.

---

# 18. Forbidden Autonomous Actions

Agents must never autonomously perform destructive operations such as:

- `git reset --hard`
- `git clean`
- Force pushing.
- Deleting branches.
- Rewriting Git history.
- Deleting user changes.
- Dropping production tables.
- Destructive database migrations.
- Removing security controls.

---

# 19. Context Preservation

When an agent modifies the project, it should preserve:

- Existing behavior.
- Existing API contracts.
- Existing tests.
- Existing configuration.
- Existing architecture.

Unless the task explicitly requires changing them.

---

# 20. Scope Control

Agents must not expand the task unnecessarily.

For example:

If the task is:

> Fix an error in RSS parsing.

Do not automatically:

- Rewrite the entire parser.
- Replace `feedparser`.
- Redesign the source architecture.
- Introduce microservices.
- Rewrite unrelated tests.

Only address broader issues if they are required for correctness or explicitly requested.

---

# 21. Dependency Introduction

If a new dependency appears necessary:

Stop before installing it.

Explain:

- Dependency name.
- Problem solved.
- Why existing dependencies are insufficient.
- Security considerations.
- Maintenance implications.
- Deployment impact.

Ask for approval when the dependency has meaningful project impact.

---

# 22. Database Changes

Database changes require special handling.

If a task requires:

- New tables.
- New columns.
- Constraints.
- Indexes.
- Data migrations.
- Data deletion.
- Schema changes.

The agent must first explain the required change.

Do not directly perform destructive database changes.

After approval:

1. Create the migration.
2. Update persistence code.
3. Update tests.
4. Validate compatibility.
5. Document the change.

---

# 23. AI Changes

AI-related changes should follow:

AI Engineer
    ↓
QA
    ↓
Security if applicable
    ↓
Code Reviewer

For significant AI architecture changes:

Architect
    ↓
User approval
    ↓
AI Engineer
    ↓
QA
    ↓
Security
    ↓
Code Reviewer

---

# 24. Security-Sensitive Changes

Security-sensitive changes should follow:

Implementation Agent
    ↓
Security
    ↓
QA
    ↓
Code Reviewer

If the security issue affects architecture:

Architect
    ↓
Security
    ↓
User approval if required
    ↓
Implementation
    ↓
QA
    ↓
Code Reviewer

---

# 25. Bug Fixes

Preferred flow:

Bug
    ↓
Root cause analysis
    ↓
Regression test
    ↓
Implementation
    ↓
QA
    ↓
Security if applicable
    ↓
Code Reviewer

Avoid architectural changes unless the bug demonstrates a real architectural problem.

---

# 26. Feature Development

Preferred flow:

Feature request
    ↓
Task classification
    ↓
Architect if necessary
    ↓
Implementation
    ↓
Tests
    ↓
Security if applicable
    ↓
Code Review
    ↓
Completion

---

# 27. Review Loop

If Code Reviewer returns:

## APPROVED

Finish.

## APPROVED WITH NOTES

Finish if notes are non-blocking.

## CHANGES REQUESTED

Return the task to the appropriate implementation agent.

Then:

Implementation
    ↓
Tests
    ↓
Code Review again

---

## BLOCKED

Stop.

Explain:

- Blocking issue.
- Why it blocks completion.
- Required decision or correction.

Do not bypass the blocker.

---

# 28. Test Failures

If tests fail:

Do not immediately modify the tests.

Determine whether the failure comes from:

- Incorrect implementation.
- Incorrect test.
- Outdated expectation.
- Environment.
- External dependency.
- Existing unrelated failure.

Tests must not be weakened simply to make the build pass.

---

# 29. Existing Test Failures

If the project already contains failing tests unrelated to the current task:

Do not silently modify them.

Report:

- Failing test.
- Cause if known.
- Whether it is related to the current change.

The current task may still be completed if the failure is demonstrably unrelated.

---

# 30. Completion Gate

A task can be considered complete only when:

- Implementation is complete.
- Relevant tests pass.
- Required security checks pass.
- Architecture is acceptable.
- No blocking review findings remain.
- Documentation is updated when required.

---

# 31. Final Response

The final response should contain:

## Summary

Short description of what changed.

## Agents involved

List the agents that participated.

## Files changed

List relevant files.

## Tests

List tests executed and their result.

## Security

State whether Security Agent was involved and its result.

## Architecture

State whether Architect was involved and whether an architectural decision was made.

## Review

State the Code Reviewer result.

## Remaining issues

List known non-blocking issues.

Do not claim the task is complete if a blocking issue remains.

---

# 32. General Rule

The agents should behave as a team of specialists, not as independent autonomous developers.

The preferred behavior is:

> Analyze → specialize → implement → test → secure → review → complete.

Keep the process lightweight for small changes and progressively more rigorous as project impact increases.

Never introduce complexity merely because additional agents are available.