============================================================
FILE: .github/workflows/feature-development.md
============================================================

# Feature Development Workflow

## Purpose

Define the standard workflow for implementing a new feature in OportunidadBot.

This workflow coordinates the existing specialized agents:

- Architect
- Backend
- AI Engineer
- QA
- Security
- Code Reviewer

The workflow must prioritize small, controlled and testable changes.

---

## 1. Initial task analysis

Start by understanding:

- The requested functionality.
- The expected behavior.
- Existing related functionality.
- Existing architecture.
- Existing tests.
- Existing contracts.
- Potential external integrations.

Before modifying code, inspect the relevant existing implementation.

Do not assume that a new implementation is required.

Always search for reusable functionality first.

---

## 2. Determine complexity

Classify the task as:

### SMALL

Examples:

- Small bug-free enhancement.
- Minor validation.
- Small endpoint modification.
- Small UI/backend adjustment.
- Local refactor.

The task can proceed directly to implementation after inspecting the relevant code.

### MEDIUM

Examples:

- New service.
- New endpoint.
- New source.
- New business logic.
- Significant database interaction.
- New AI functionality.

The task should involve the relevant specialist agents.

### LARGE

Examples:

- New subsystem.
- Significant architecture change.
- New external infrastructure.
- New provider.
- Major persistence changes.
- Major AI architecture.
- Changes affecting multiple modules.

The task requires architectural analysis before implementation.

---

## 3. Architect analysis

For MEDIUM and LARGE tasks, involve the Architect Agent.

The Architect should determine:

- Where the functionality belongs.
- Which existing components should be reused.
- Which components should change.
- Whether a new abstraction is necessary.
- Whether existing contracts are affected.
- Whether the task introduces architectural risk.

The Architect must avoid unnecessary architecture.

The current project should remain a modular monolith unless there is a concrete reason to change this.

---

## 4. Architectural approval

Stop and ask the user for confirmation before:

- Introducing microservices.
- Splitting applications.
- Merging applications.
- Changing persistence technology.
- Replacing Supabase.
- Replacing FastAPI.
- Replacing Telegram.
- Replacing Stripe.
- Replacing Railway.
- Introducing a formal architecture.
- Changing important API contracts.
- Introducing major infrastructure.

Do not make these decisions autonomously.

---

## 5. Implementation agent selection

Select the appropriate specialist.

### Backend

Use Backend Agent for:

- FastAPI.
- Python.
- Services.
- Database integration.
- Telegram backend logic.
- Scheduler.
- External integrations.

### AI Engineer

Use AI Engineer for:

- LLM.
- Prompt engineering.
- Classification.
- Model configuration.
- AI evaluation.
- AI cost optimization.
- AI-specific security.

### Frontend

If frontend-specific work exists, follow the frontend conventions defined in the global instructions.

Do not involve Backend Agent unnecessarily for frontend-only work.

---

## 6. Security analysis

Security review is required when the feature involves:

- User input.
- External URLs.
- Authentication.
- Authorization.
- Webhooks.
- Stripe.
- Telegram.
- Supabase.
- Sensitive information.
- AI.
- File handling.
- Network requests.

Use Security Agent when the risk is meaningful.

Security should not be treated as an afterthought.

---

## 7. QA implementation

QA Agent should determine the required testing strategy.

At minimum consider:

- Unit tests.
- Integration tests.
- Regression tests.
- E2E tests when appropriate.

Every functional change should have appropriate test coverage.

---

## 8. Implementation

The implementation agent should:

1. Reuse existing code.
2. Make the smallest reasonable change.
3. Avoid unrelated refactors.
4. Follow existing conventions.
5. Add or update tests.
6. Preserve existing contracts.
7. Keep error handling explicit.

Do not modify unrelated components.

---

## 9. Validation

After implementation:

1. Run relevant unit tests.
2. Run integration tests when appropriate.
3. Run E2E tests when appropriate.
4. Check coverage.
5. Check linting or static validation if configured.
6. Inspect the final diff.

If tests fail, determine whether:

- The implementation is wrong.
- The test is outdated.
- The test is incorrect.
- An unrelated regression exists.

Never delete tests simply to make the suite pass.

---

## 10. Security review

For security-sensitive changes:

Security Agent reviews:

- Input validation.
- Authentication.
- Authorization.
- Secrets.
- External requests.
- SSRF.
- Injection.
- Webhooks.
- Data exposure.
- Logging.

Security findings must be addressed before approval when they are blocking.

---

## 11. Code review

Code Reviewer performs the final review.

The reviewer checks:

- Correctness.
- Architecture.
- Maintainability.
- Testing.
- Security.
- Performance.
- Regression risk.
- Scope.

The reviewer should return one of:

- APPROVED
- APPROVED WITH NOTES
- CHANGES REQUESTED
- BLOCKED

---

## 12. Corrections

If Code Reviewer returns CHANGES REQUESTED:

1. Identify the findings.
2. Correct them using the appropriate specialist.
3. Run tests again.
4. Re-run Code Reviewer.

Do not introduce unrelated changes while fixing review findings.

---

## 13. Completion criteria

The feature is complete when:

- The requested behavior works.
- Relevant tests pass.
- Regression risk is controlled.
- Security concerns are addressed.
- Architecture is consistent.
- Documentation is updated when necessary.
- Code review is approved.

---

## 14. Final output

At the end, summarize:

- What was implemented.
- Files changed.
- Tests executed.
- Security review status.
- Code review status.
- Remaining notes.

Do not claim completion if blocking findings remain.


============================================================
FILE: .github/workflows/bug-fix.md
============================================================

# Bug Fix Workflow

## Purpose

Define the standard workflow for diagnosing and fixing bugs in OportunidadBot.

The priority is to identify the root cause rather than patching symptoms.

---

## 1. Reproduce the problem

Before changing code, determine:

- Expected behavior.
- Actual behavior.
- Steps to reproduce.
- Affected component.
- Error message.
- Relevant logs.
- Relevant tests.

If the bug cannot be reproduced, inspect the implementation and available evidence before making assumptions.

---

## 2. Identify the affected area

Inspect:

- Relevant service.
- Callers.
- Dependencies.
- Database interactions.
- External integrations.
- Tests.

Do not immediately modify the first suspicious line.

---

## 3. Root cause analysis

Determine whether the problem originates from:

- Input validation.
- Business logic.
- Persistence.
- External integration.
- Parsing.
- Scheduling.
- Concurrency.
- Configuration.
- AI classification.
- Telegram.
- Stripe.
- API behavior.

The goal is to identify the actual root cause.

---

## 4. Regression test

Before fixing the bug, create or update a regression test whenever practical.

The test should reproduce the incorrect behavior.

The test should fail before the fix and pass after the fix.

---

## 5. Specialist selection

Use the appropriate agent.

### Backend Agent

For:

- Python.
- FastAPI.
- Services.
- Database.
- Scheduler.
- Integrations.

### AI Engineer

For:

- LLM behavior.
- Prompt issues.
- Classification errors.
- AI output validation.
- AI provider errors.

### Security Agent

For:

- Vulnerabilities.
- Authentication.
- Authorization.
- SSRF.
- Injection.
- Secret exposure.
- Security-related bugs.

### Architect Agent

Only when the root cause indicates a broader architectural problem.

Do not turn every bug fix into an architectural redesign.

---

## 6. Implement the smallest safe fix

Prefer:

- Minimal change.
- Existing abstractions.
- Existing patterns.
- Existing utilities.

Avoid:

- Large refactors.
- New dependencies.
- New architecture.

unless required to correctly fix the problem.

---

## 7. Run tests

Run:

- Regression test.
- Relevant unit tests.
- Relevant integration tests.
- Relevant E2E tests.

Run the complete test suite when the change affects shared infrastructure or important global behavior.

---

## 8. Check for regressions

After the fix, check:

- Existing behavior.
- Related functionality.
- Error handling.
- Side effects.
- Persistence.
- External integrations.

Do not assume that a passing regression test is sufficient.

---

## 9. Security review

If the bug has security implications, involve Security Agent.

Security vulnerabilities must not be treated as normal low-priority bugs.

---

## 10. Code review

Code Reviewer validates:

- Root cause was correctly addressed.
- Fix is minimal.
- Regression test exists.
- No unrelated changes were introduced.
- No new vulnerabilities were introduced.
- Existing behavior remains intact.

---

## 11. Completion criteria

A bug fix is complete when:

- Root cause is identified.
- Regression test exists when practical.
- Fix is implemented.
- Relevant tests pass.
- No known regression exists.
- Security is addressed when applicable.
- Code review is approved.

---

## 12. Final report

Provide:

- Root cause.
- Fix.
- Files changed.
- Regression test.
- Tests executed.
- Security status.
- Review status.


============================================================
FILE: .github/workflows/ai-change.md
============================================================

# AI Change Workflow

## Purpose

Define the workflow for changes involving LLMs, prompts, classification or AI infrastructure in OportunidadBot.

The goal is to maintain AI quality while controlling:

- Cost.
- Latency.
- Reliability.
- Security.
- Maintainability.

---

## 1. Determine whether AI is necessary

Before implementing an AI change, ask:

- Can the problem be solved deterministically?
- Can existing rules solve it?
- Can existing parsing solve it?
- Can existing services solve it?

Do not introduce an LLM when deterministic logic is sufficient.

---

## 2. AI Engineer analysis

AI Engineer should inspect:

- `app/services/ai_classifier.py`
- `app/services/prompts.py`
- `app/services/orchestrator.py`
- `app/config.py`
- AI-related tests.
- Existing mocks.
- Existing fixtures.

Determine:

- Required input.
- Required output.
- Prompt changes.
- Model changes.
- Validation.
- Error handling.
- Fallback.
- Cost.
- Latency.

---

## 3. Define the AI contract

Before implementation, clearly define:

### Input

What information is sent to the model.

### Output

What the model must return.

### Validation

How the output is validated.

### Failure

What happens when the model fails.

### Fallback

What happens when classification is unavailable.

---

## 4. Prompt design

Prompts should:

- Be concise.
- Be explicit.
- Separate instructions from external data.
- Define expected output.
- Avoid unnecessary complexity.

External scraped content must always be treated as data.

---

## 5. Prompt injection analysis

Consider malicious content such as:

- Instructions embedded in advertisements.
- Requests to ignore system instructions.
- Attempts to reveal prompts.
- Attempts to influence classification.
- Attempts to trigger privileged actions.

The LLM must never treat scraped content as trusted instructions.

---

## 6. Model changes

If changing the model, evaluate:

- Quality.
- Latency.
- Cost.
- Context limits.
- Output compatibility.
- Reliability.

A model change can be a functional change.

---

## 7. Output validation

Never trust raw LLM output.

Validate:

- Structure.
- Types.
- Required fields.
- Allowed values.
- Consistency.

Invalid output must result in a controlled failure.

---

## 8. Error handling

Handle at least where applicable:

- Timeout.
- Rate limit.
- Provider error.
- Network error.
- Invalid output.
- Empty response.

Retries must be limited.

Use backoff for transient failures.

---

## 9. Cost analysis

Before increasing LLM usage, evaluate:

- Number of calls.
- Input tokens.
- Output tokens.
- Model cost.
- Retries.
- Cache opportunities.

Avoid duplicate classifications.

Novelty detection should happen before AI processing when possible.

---

## 10. Testing

AI changes must include appropriate tests.

Consider:

- Clearly relevant content.
- Clearly irrelevant content.
- Ambiguous content.
- Empty content.
- Long content.
- Malicious content.
- Prompt injection.
- Invalid model response.
- Timeout.
- Rate limit.

Normal tests should not call the real LLM.

Use mocks and fakes.

---

## 11. Evaluation

For significant prompt or model changes, evaluate representative examples.

Consider:

- Precision.
- Recall.
- F1.
- False positives.
- False negatives.

Do not evaluate based on one example.

---

## 12. Regression protection

If an AI change fixes a known classification problem:

Add a regression example.

Ensure future prompt/model changes can be tested against it.

---

## 13. Security

Security Agent should review AI changes involving:

- User-controlled prompts.
- Sensitive data.
- External content.
- Generated URLs.
- Tool calling.
- New external services.

---

## 14. Architecture

Architect Agent should be consulted before:

- Introducing multiple providers.
- Introducing RAG.
- Introducing vector databases.
- Introducing agent frameworks.
- Introducing tool calling.
- Introducing autonomous agents.
- Creating major AI infrastructure.

Do not introduce these technologies simply because they are available.

---

## 15. Code review

Code Reviewer verifies:

- Correctness.
- Tests.
- Security.
- Prompt injection handling.
- Cost.
- Latency.
- Error handling.
- Maintainability.

---

## 16. Completion criteria

An AI change is complete when:

- AI is genuinely necessary.
- Input is controlled.
- Prompt is maintainable.
- Output is validated.
- Errors are handled.
- Tests pass.
- Security is considered.
- Cost is reasonable.
- Latency is reasonable.
- Code review passes.


============================================================
FILE: .github/workflows/code-review.md
============================================================

# Code Review Workflow

## Purpose

Define the standard workflow for reviewing changes in OportunidadBot.

Code Review is the final quality gate.

---

## 1. Review scope

First determine:

- What changed.
- Why it changed.
- Which files changed.
- Which components are affected.
- Which contracts are affected.

Do not review unrelated parts of the project.

---

## 2. Context inspection

Inspect relevant:

- Services.
- Callers.
- Tests.
- Configuration.
- Models.
- Database operations.
- External integrations.

Understand the existing behavior before judging the new implementation.

---

## 3. Functional review

Check:

- Expected behavior.
- Edge cases.
- Error handling.
- Side effects.
- Idempotency.
- Duplicate processing.
- Backward compatibility.

---

## 4. Architecture review

Check:

- Responsibilities.
- Dependencies.
- Existing module boundaries.
- Reuse.
- Complexity.
- Unnecessary abstractions.

The project should remain a modular monolith unless explicitly approved otherwise.

---

## 5. Security review

Check:

- Secrets.
- Authentication.
- Authorization.
- Input validation.
- SSRF.
- Injection.
- Webhooks.
- Data exposure.
- Logs.

For significant security concerns involve Security Agent.

---

## 6. Testing review

Check:

- Tests were added or updated.
- Tests verify behavior.
- Error paths are covered.
- Regression tests exist for bug fixes.
- External services are mocked appropriately.
- Tests are deterministic.

Do not approve tests that only increase coverage without validating behavior.

---

## 7. Performance review

Check:

- Duplicate requests.
- Expensive operations.
- Database queries.
- Concurrency.
- Memory usage.
- External API calls.
- AI calls.

Do not optimize code without a meaningful reason.

---

## 8. Maintainability review

Check:

- Naming.
- Function complexity.
- Duplication.
- Coupling.
- Error handling.
- Configuration.
- Documentation.

Do not impose personal coding preferences.

---

## 9. Diff review

Look for:

- Unrelated changes.
- Accidental modifications.
- Large formatting changes.
- Deleted tests.
- Deleted functionality.
- Debug code.
- Temporary code.
- Secrets.

---

## 10. AI-specific review

If AI is involved, check:

- Prompt.
- Input.
- Output.
- Validation.
- Retries.
- Timeout.
- Cost.
- Prompt injection.
- Regression tests.

Use AI Engineer for specialized analysis.

---

## 11. Findings

Each finding should include:

- Severity.
- Location.
- Problem.
- Impact.
- Recommendation.

Avoid vague findings.

---

## 12. Severity

Use:

### CRITICAL

Security compromise, data corruption, destructive behavior or severe production failure.

### HIGH

Important regression, security issue, broken contract or major reliability problem.

### MEDIUM

Meaningful maintainability, correctness or testing problem.

### LOW

Minor improvement that does not block the change.

---

## 13. Verdict

Return one:

### APPROVED

No relevant blocking issues.

### APPROVED WITH NOTES

No blocking issues, but improvements are recommended.

### CHANGES REQUESTED

One or more issues must be fixed.

### BLOCKED

A critical issue or explicit architectural/security decision prevents approval.

---

## 14. Corrections

If corrections are requested:

1. Fix the findings.
2. Run relevant tests.
3. Review the diff again.
4. Re-run Code Review.

Do not introduce unrelated changes.

---

## 15. Final review report

Provide:

### Verdict

Final status.

### Findings

Relevant issues.

### Tests

Tests executed and result.

### Security

Security review result.

### Architecture

Architecture review result.

### Recommendation

Final recommendation.


============================================================
FILE: .github/workflows/architectural-change.md
============================================================

# Architectural Change Workflow

## Purpose

Define the workflow for changes that may significantly affect the architecture of OportunidadBot.

Architectural changes require explicit reasoning and user approval.

---

## 1. Detect architectural changes

Treat a change as potentially architectural when it involves:

- New applications.
- Microservices.
- New infrastructure.
- New database technology.
- Changing persistence architecture.
- Changing FastAPI.
- Changing Telegram integration.
- Changing Stripe integration.
- Changing Railway.
- New message brokers.
- New queues.
- New distributed systems.
- Major API contract changes.
- Major AI infrastructure.
- RAG.
- Vector databases.
- Agent frameworks.
- Autonomous agents.
- Major module restructuring.

---

## 2. Architect analysis

Architect Agent should inspect:

- Current architecture.
- Existing module boundaries.
- Dependencies.
- Data flow.
- Deployment model.
- Testing.
- Observability.
- Operational complexity.

---

## 3. Current architectural baseline

The current system should be treated as:

A modular monolith.

The main application contains:

- FastAPI.
- Telegram bot.
- Scheduled jobs.
- Scraping sources.
- Services.
- Persistence.
- Debugging/traceability.

Do not assume distributed architecture is required.

---

## 4. Architecture principles

Prefer:

- Simplicity.
- Modularity.
- Clear responsibilities.
- Reuse.
- Low operational overhead.
- Existing infrastructure.

Avoid:

- Premature microservices.
- Distributed systems without need.
- New infrastructure without measurable benefit.
- Excessive abstraction.

---

## 5. Alternatives

For significant changes, Architect Agent should consider:

### Option A

Keep the current architecture.

### Option B

Small modular improvement.

### Option C

Major architectural change.

Prefer the simplest option that solves the problem.

---

## 6. Decision criteria

Evaluate:

- Complexity.
- Maintenance.
- Scalability.
- Reliability.
- Security.
- Performance.
- Development speed.
- Operational cost.
- Deployment complexity.
- Testing complexity.

---

## 7. User approval required

The agent must ask the user before implementing:

- Microservices.
- Database replacement.
- Major persistence changes.
- New infrastructure.
- Major API contract changes.
- New deployment architecture.
- Major AI architecture.
- New external platform dependencies.

Do not make these decisions autonomously.

---

## 8. ADR

If the decision has long-term architectural consequences, create or update an ADR.

The ADR should explain:

- Context.
- Problem.
- Options considered.
- Decision.
- Reasons.
- Consequences.

Do not create ADRs for trivial implementation details.

---

## 9. Implementation

After approval:

1. Define the target architecture.
2. Identify affected modules.
3. Define migration strategy if required.
4. Implement incrementally.
5. Preserve compatibility where possible.
6. Add tests.
7. Update documentation.
8. Review security.
9. Review performance.

---

## 10. Migration safety

If existing data or functionality is affected:

- Avoid destructive migrations where possible.
- Preserve existing data.
- Provide a migration path.
- Validate existing records.
- Consider rollback.
- Test migration behavior.

Database changes require explicit approval.

---

## 11. Security

Security Agent should review architectural changes that affect:

- Authentication.
- Authorization.
- Network boundaries.
- External services.
- Secrets.
- Data storage.
- Webhooks.
- User data.

---

## 12. QA

QA Agent should review:

- New test strategy.
- Integration boundaries.
- E2E impact.
- Regression coverage.
- Migration testing.

---

## 13. Code Review

Code Reviewer performs the final implementation review.

Review:

- Architecture.
- Implementation.
- Testing.
- Security.
- Performance.
- Documentation.

---

## 14. Completion criteria

Architectural work is complete when:

- Architecture decision is documented when appropriate.
- User approval was obtained when required.
- Implementation matches the approved design.
- Tests pass.
- Security has been reviewed.
- Documentation is updated.
- Code Review approves the implementation.

---

## 15. Final output

Provide:

- Architectural decision.
- Reasoning.
- Components affected.
- Files changed.
- Migration impact.
- Tests.
- Security status.
- Documentation status.
- Code review status.

Never claim an architectural change is complete while required approval is missing.