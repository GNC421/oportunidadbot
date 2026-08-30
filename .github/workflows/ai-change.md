# AI Change Workflow

## Purpose

Define the standard workflow for implementing, modifying, evaluating and reviewing AI-related functionality in OportunidadBot.

This workflow applies to changes involving:

- Large Language Models (LLMs).
- AI classification.
- Prompts.
- AI providers.
- Model configuration.
- AI output parsing.
- AI output validation.
- AI evaluation.
- AI reliability.
- AI performance.
- AI cost optimization.
- AI security.
- Prompt injection protection.

The objective is to introduce AI functionality in a controlled, measurable and maintainable way.

AI should only be used when it provides a meaningful advantage over deterministic logic.

---

## 1. Initial AI Task Analysis

Before modifying AI-related code, determine:

- What problem the AI functionality is solving.
- Why AI is required.
- What existing deterministic logic already exists.
- What input is sent to the model.
- What output is expected.
- Where the AI functionality is invoked.
- What happens when the AI is unavailable.
- What tests already exist.
- What external provider is being used.
- What potential security implications exist.

Inspect the existing implementation before creating new abstractions.

---

## 2. Determine Whether AI Is Necessary

Before introducing or expanding AI usage, consider whether the problem can be solved using:

- Existing business rules.
- Regular expressions.
- Existing parsers.
- Existing normalization.
- Existing source-specific logic.
- Database queries.
- Deterministic classification.
- Existing application services.

Do not introduce an LLM when deterministic logic is sufficient.

AI should be introduced when ambiguity, semantic understanding or another concrete requirement justifies it.

---

## 3. AI Engineer Agent

The AI Engineer Agent is responsible for AI-specific implementation and analysis.

Use the AI Engineer Agent for:

- Prompt design.
- Prompt modifications.
- Model selection.
- Model configuration.
- LLM integration.
- AI classification.
- Output parsing.
- Output validation.
- AI evaluation.
- AI performance.
- AI cost.
- AI latency.
- AI reliability.
- AI-specific error handling.
- Prompt injection analysis.

The AI Engineer should reuse the existing AI implementation before creating new infrastructure.

---

## 4. Existing AI Architecture

Before changing the AI implementation, inspect the existing components.

Relevant areas currently include:

- `app/services/ai_classifier.py`
- `app/services/prompts.py`
- `app/services/orchestrator.py`
- `app/config.py`
- AI-related tests.
- NVIDIA/OpenAI-compatible integration.
- Existing AI mocks and fakes.
- Existing classification fixtures.

Do not create another AI abstraction if an existing one already provides the required functionality.

---

## 5. AI Contract

Every AI interaction should have a clearly defined contract.

The contract should specify:

### Input

Define:

- What data is sent to the model.
- Which fields are required.
- Which fields are optional.
- Maximum relevant content.
- Any preprocessing or normalization.

### Output

Define:

- Expected structure.
- Required fields.
- Allowed values.
- Types.
- Default behavior.

### Validation

Define how the model response is validated before being used by the application.

### Failure

Define what happens when:

- The model fails.
- The provider is unavailable.
- The response is invalid.
- The request times out.
- The request is rate-limited.

### Fallback

Define whether the system can continue without AI.

---

## 6. AI Must Not Control Application Logic Directly

The LLM must not be treated as a trusted source of executable instructions.

AI output should be treated as untrusted data.

The application must remain responsible for:

- Validation.
- Business rules.
- Authorization.
- Security decisions.
- Persistence.
- External actions.

Never allow an LLM response to bypass application-level validation.

---

## 7. Prompt Design

Prompts should be:

- Explicit.
- Focused.
- Maintainable.
- Deterministic where possible.
- Easy to understand.
- Easy to test.

Prompts should clearly separate:

- Instructions.
- Context.
- External content.
- Expected output.

Avoid unnecessarily long prompts.

Avoid duplicating instructions that can be enforced by application code.

---

## 8. External Content Is Untrusted

Scraped content must always be considered untrusted input.

This includes content originating from:

- RSS feeds.
- Reddit.
- Tablón de Anuncios.
- User-provided sources.
- External websites.
- Advertisements.
- Comments.
- Titles.
- Descriptions.

External content must never be treated as system instructions.

---

## 9. Prompt Injection Protection

AI functionality must consider prompt injection.

Potential malicious content may attempt to:

- Override instructions.
- Change classification.
- Reveal prompts.
- Reveal internal information.
- Manipulate the model.
- Trigger unintended behavior.
- Cause the model to ignore its task.
- Inject fake system messages.

The AI system should clearly distinguish between:

- Trusted instructions.
- Untrusted external content.

Do not rely solely on the model to protect against prompt injection.

Application-level validation should remain in place.

---

## 10. Model Selection

When selecting or changing a model, evaluate:

- Accuracy.
- Classification quality.
- Latency.
- Cost.
- Context size.
- Output reliability.
- Provider availability.
- Compatibility with the existing integration.

Do not change models simply because a newer model exists.

A model change may alter application behavior and should therefore be treated as a functional change.

---

## 11. Model Configuration

Model configuration should be centralized where practical.

Do not hardcode:

- API keys.
- Tokens.
- Credentials.
- Environment-specific configuration.

Use the existing configuration system and environment variables.

Do not commit production credentials.

---

## 12. AI Provider

The current AI integration uses an NVIDIA API through an OpenAI-compatible SDK.

Before modifying the provider integration, inspect the existing implementation.

Do not replace the provider without:

1. Understanding the current integration.
2. Evaluating alternatives.
3. Considering cost.
4. Considering latency.
5. Considering compatibility.
6. Considering deployment impact.
7. Obtaining required approval.

---

## 13. Provider Failure

The AI provider must be treated as an external and potentially unreliable dependency.

Consider:

- Network failures.
- Timeouts.
- Rate limits.
- Authentication errors.
- Invalid responses.
- Service outages.
- Unexpected response formats.

The application should fail gracefully whenever possible.

---

## 14. Retry Strategy

Retries should only be used when they provide a meaningful benefit.

Retries must:

- Be bounded.
- Avoid infinite loops.
- Prefer transient errors.
- Use appropriate delays or backoff.
- Avoid multiplying AI costs unnecessarily.

Do not retry every error indiscriminately.

Invalid model output should not necessarily trigger unlimited retries.

---

## 15. Timeout Strategy

AI requests should have appropriate timeouts.

Do not allow a failed AI provider to block the complete processing pipeline indefinitely.

When an AI request times out:

- Log the failure appropriately.
- Preserve traceability.
- Apply the configured fallback.
- Avoid exposing sensitive information.

---

## 16. Output Validation

Never trust raw LLM output.

Validate:

- Response existence.
- Structure.
- Types.
- Required fields.
- Allowed values.
- Length where relevant.
- Semantic constraints where applicable.

Invalid output should result in controlled handling.

Do not blindly pass raw model output to:

- Database operations.
- Telegram messages.
- APIs.
- HTML.
- External services.
- Application commands.

---

## 17. Structured Output

When structured output is expected, define the schema explicitly.

Prefer predictable formats over free-form responses.

If the existing implementation expects a specific structure, preserve compatibility unless the task explicitly requires changing it.

---

## 18. AI Classification

For classification functionality, clearly define:

- Classification categories.
- Meaning of each category.
- Input requirements.
- Expected output.
- Unknown/uncertain behavior.
- Fallback behavior.

Do not silently change classification semantics.

If a category is renamed or removed, treat it as a behavioral change.

---

## 19. Classification Pipeline

Where applicable, preserve the following conceptual flow:

Sources
→ Parsing
→ Normalization
→ Novelty Detection
→ AI Classification
→ Persistence
→ Alert

AI should not run unnecessarily.

Novelty detection should occur before AI classification when possible.

Avoid classifying the same content repeatedly.

---

## 20. AI Caching

Before implementing AI caching, determine:

- Whether the same content can be classified repeatedly.
- What identifies equivalent input.
- How cache invalidation works.
- Whether prompt/model changes invalidate previous results.
- Whether cached results remain valid.

Do not introduce caching merely for perceived performance.

If caching is implemented, ensure stale classifications cannot silently produce incorrect behavior.

---

## 21. AI Cost

Every AI change should consider cost.

Evaluate:

- Number of AI calls.
- Input size.
- Output size.
- Model pricing.
- Retry frequency.
- Duplicate requests.
- Cache opportunities.
- Processing volume.

Prefer reducing unnecessary AI calls before optimizing model parameters.

Do not increase AI usage significantly without understanding the cost impact.

---

## 22. AI Latency

Consider the impact of AI on the complete processing pipeline.

Evaluate:

- Average response time.
- Timeout behavior.
- Concurrent requests.
- Scheduler execution.
- User-facing alert latency.

AI should not unnecessarily block unrelated processing.

---

## 23. AI Reliability

AI functionality should be considered probabilistic.

Do not assume that the model will always:

- Follow instructions.
- Return valid output.
- Classify correctly.
- Respond within the expected time.
- Return consistent results.

The application must handle uncertainty.

---

## 24. AI Fallback

Where appropriate, define a fallback when AI is unavailable.

Possible strategies include:

- Skip classification.
- Mark classification as unknown.
- Use deterministic rules.
- Continue processing without AI.
- Retry a limited number of times.

The fallback must be compatible with existing business behavior.

Do not invent fallback behavior without understanding the application's requirements.

---

## 25. AI Security

AI Engineer should involve Security Agent when changes affect:

- User-controlled prompts.
- Sensitive data.
- External content.
- Prompt injection.
- Tool calling.
- Generated URLs.
- External actions.
- Authentication.
- Authorization.
- Secrets.
- New AI providers.

Security requirements take precedence over convenience.

---

## 26. Sensitive Data

Do not send unnecessary sensitive information to an external AI provider.

Before sending data to the model, determine:

- Whether the data is necessary.
- Whether it contains secrets.
- Whether it contains credentials.
- Whether it contains private user information.
- Whether it contains internal application information.

Send the minimum information required to perform the task.

---

## 27. Logging AI Requests

AI-related logs should provide enough information to diagnose failures without exposing sensitive data.

Do not log:

- API keys.
- Tokens.
- Credentials.
- Secrets.
- Sensitive user information.
- Complete sensitive prompts.
- Complete sensitive model responses.

Prefer structured metadata such as:

- Request identifier.
- Model.
- Execution time.
- Success/failure.
- Classification result where safe.
- Error category.

---

## 28. AI Testing

AI changes must include appropriate automated tests.

Tests should not normally depend on a live external LLM.

Use:

- Mocks.
- Fakes.
- Fixtures.
- Deterministic test responses.

Live AI tests may exist separately when explicitly justified.

---

## 29. Unit Tests

Unit tests should cover:

- Prompt construction.
- Input preprocessing.
- Output parsing.
- Output validation.
- Classification logic.
- Error handling.
- Retry behavior.
- Fallback behavior.

Tests should be deterministic.

---

## 30. Integration Tests

Integration tests should verify interactions between:

- AI service.
- Orchestrator.
- Persistence.
- Configuration.
- Other relevant services.

Use controlled AI responses where possible.

Do not make the normal test suite dependent on an external provider.

---

## 31. End-to-End Tests

Use E2E tests when AI behavior affects a critical complete workflow.

For example:

Source
→ Parsing
→ Novelty Detection
→ AI Classification
→ Persistence
→ Telegram Alert

E2E tests should remain deterministic where possible.

---

## 32. AI Test Cases

Consider tests for:

- Clearly relevant content.
- Clearly irrelevant content.
- Ambiguous content.
- Empty input.
- Missing fields.
- Very long input.
- Invalid model response.
- Malformed structured output.
- Provider timeout.
- Provider error.
- Rate limiting.
- Prompt injection attempts.
- Unexpected model behavior.

Only add cases that provide meaningful protection.

---

## 33. Regression Tests

When an AI change fixes an existing classification problem:

Add a regression example.

The example should represent the previously incorrect behavior.

Future prompt or model changes should be tested against important historical failures.

---

## 34. AI Evaluation

For significant changes to prompts or models, evaluate representative examples.

Consider:

- Accuracy.
- Precision.
- Recall.
- F1 score.
- False positives.
- False negatives.

The evaluation dataset should contain varied examples.

Do not judge a model or prompt based on a single example.

---

## 35. Prompt Changes

A prompt change can alter application behavior.

When modifying prompts:

1. Understand the current behavior.
2. Identify the desired behavior.
3. Update the prompt.
4. Update relevant tests.
5. Evaluate representative examples.
6. Check for regressions.
7. Review cost and latency.

Do not modify prompts simply to make one isolated example pass.

---

## 36. Model Changes

When changing the model:

1. Identify why the change is necessary.
2. Compare expected behavior.
3. Evaluate representative examples.
4. Check output compatibility.
5. Check latency.
6. Check cost.
7. Update tests.
8. Review security implications.

A model upgrade should not be assumed to be behaviorally equivalent.

---

## 37. New AI Dependencies

Avoid introducing AI frameworks or dependencies unless necessary.

Before adding a dependency, explain:

- What problem it solves.
- Why the current implementation is insufficient.
- Why the standard library or existing dependencies cannot solve it.
- Maintenance implications.
- Security implications.
- Deployment impact.
- Performance implications.

Significant dependencies require user approval.

---

## 38. AI Frameworks

Do not introduce an agent framework, orchestration framework, RAG framework, vector database or similar technology merely because the project uses AI.

Such technologies should only be introduced when there is a concrete requirement.

Major AI architecture changes require Architect Agent analysis.

---

## 39. RAG and Vector Databases

If a task proposes:

- RAG.
- Embeddings.
- Vector databases.
- Semantic search.
- Document retrieval.

First determine whether the requirement genuinely needs these capabilities.

Before implementation:

1. Involve Architect Agent.
2. Evaluate simpler alternatives.
3. Consider infrastructure.
4. Consider cost.
5. Consider data lifecycle.
6. Consider security.
7. Ask the user for approval when required.

---

## 40. Agentic AI

If a task proposes autonomous agents or tool-calling systems:

Do not implement immediately.

First evaluate:

- Required autonomy.
- Available tools.
- Permissions.
- Security boundaries.
- Failure modes.
- Cost.
- Observability.
- Human approval requirements.

Architect Agent and Security Agent should be involved.

Major agentic architecture requires explicit user approval.

---

## 41. Architecture Escalation

Involve Architect Agent when an AI change affects:

- Application boundaries.
- New infrastructure.
- Multiple AI providers.
- Persistent AI state.
- Vector databases.
- RAG.
- Agent frameworks.
- Tool calling.
- Autonomous agents.
- Major orchestration changes.

Do not allow AI requirements to automatically justify architectural complexity.

---

## 42. QA Review

QA Agent should review AI changes for:

- Test coverage.
- Regression protection.
- Edge cases.
- Failure scenarios.
- Integration behavior.
- E2E impact.

QA should challenge assumptions about deterministic AI behavior.

---

## 43. Security Review

Security Agent should review applicable AI changes for:

- Prompt injection.
- Data leakage.
- External content handling.
- Secrets.
- Unauthorized actions.
- Unsafe generated content.
- SSRF.
- Tool execution.
- External requests.

Critical and high-severity security findings block completion.

---

## 44. Code Review

Code Reviewer should perform the final review.

The review should verify:

- Correctness.
- Maintainability.
- Prompt quality.
- Output validation.
- Error handling.
- Tests.
- Security.
- Cost.
- Latency.
- Regression risk.
- Architectural consistency.

---

## 45. AI Change Workflow

The preferred workflow is:

AI Requirement
→ Determine whether AI is necessary
→ Inspect existing AI implementation
→ AI Engineer analysis
→ Architect if architectural impact exists
→ User approval if required
→ Implementation
→ Automated tests
→ AI evaluation when applicable
→ Security review when applicable
→ Code Review
→ Completion

---

## 46. Small AI Changes

For small changes such as:

- Minor prompt correction.
- Small validation improvement.
- Local error handling.
- Small test improvement.

The AI Engineer may proceed directly after inspecting the existing implementation.

Do not invoke every agent unnecessarily.

---

## 47. Medium AI Changes

For changes such as:

- New classification behavior.
- New AI service.
- New model.
- Significant prompt redesign.
- New fallback strategy.

Preferred flow:

AI Engineer
→ QA
→ Security if applicable
→ Code Reviewer

Architect should be involved if architecture is affected.

---

## 48. Large AI Changes

For changes such as:

- New AI subsystem.
- Multiple AI providers.
- RAG.
- Vector database.
- Agent framework.
- Autonomous agents.
- Tool calling.
- Major orchestration changes.

Preferred flow:

Architect
→ User approval
→ AI Engineer
→ QA
→ Security
→ Code Reviewer

Do not bypass the approval stage.

---

## 49. AI Change Review Verdict

Code Reviewer should return one of:

### APPROVED

The change is acceptable.

### APPROVED WITH NOTES

The change is acceptable but contains non-blocking recommendations.

### CHANGES REQUESTED

The implementation requires corrections.

### BLOCKED

A critical problem prevents completion.

---

## 50. Changes Requested

If Code Reviewer requests changes:

1. Review the findings.
2. Determine the appropriate specialist.
3. Implement only the required corrections.
4. Run relevant tests.
5. Re-evaluate AI behavior when necessary.
6. Review the final diff.
7. Run Code Reviewer again.

Do not introduce unrelated AI improvements during this process.

---

## 51. Production Considerations

Before enabling significant AI behavior in production, verify:

- Model configuration.
- Environment variables.
- Provider availability.
- Timeouts.
- Retry limits.
- Error handling.
- Cost expectations.
- Logging.
- Monitoring.
- Fallback behavior.

Do not expose production credentials.

---

## 52. Release Considerations

For significant AI changes, confirm:

- Tests pass.
- Regression examples pass.
- AI evaluation is acceptable.
- Security review is complete.
- Code Review is approved.
- Configuration is correct.
- Cost impact is understood.
- Latency impact is understood.

---

## 53. Completion Criteria

An AI change is complete only when:

- AI is justified for the problem.
- Existing functionality was reused where appropriate.
- Input is controlled.
- External content is treated as untrusted.
- Prompt is maintainable.
- Output is validated.
- Errors are handled.
- Fallback behavior is defined where necessary.
- Tests pass.
- Regression protection exists where appropriate.
- Security has been reviewed when applicable.
- Cost impact is understood.
- Latency impact is understood.
- Architectural approval was obtained when required.
- Code Review has no blocking findings.

---

## 54. Final Report

When the AI change is complete, provide:

### Summary

Explain what changed.

### AI Behavior

Explain how AI behavior changed.

### Files Changed

List the relevant files.

### Model

Identify the model involved when relevant.

### Prompt

Describe the prompt changes when relevant.

### Tests

List tests executed and their results.

### Evaluation

Summarize AI evaluation results when applicable.

### Security

State whether Security Agent reviewed the change.

### Architecture

State whether Architect Agent was involved.

### Cost

Mention relevant cost implications when applicable.

### Latency

Mention relevant latency implications when applicable.

### Code Review

State the final review verdict.

### Remaining Issues

List known non-blocking issues.

---

## 55. General Rule

AI must remain a controlled component of the application.

The preferred approach is:

Understand the problem
→ Determine whether AI is necessary
→ Reuse existing AI infrastructure
→ Define the contract
→ Protect against untrusted input
→ Validate model output
→ Test
→ Evaluate
→ Secure
→ Review
→ Complete

Do not introduce AI complexity merely because an LLM can technically solve the problem.

The application remains responsible for correctness, security and business decisions.