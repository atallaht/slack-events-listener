# Linear → GitHub Delivery Loop

Deliver a Linear issue through a GitHub pull request with a repeatable,
self-documenting workflow. This repo copy is editable; the loaded skill lives
at `~/.hermes/skills/software-development/linear-github-delivery-loop/SKILL.md`.

## Trigger

User says any of:
- "Start on this Linear issue."
- "Work on LINEAR-123."
- "Deliver the issue from Linear."
- "Implement the Linear issue."

Hermes will load the `linear-github-delivery-loop` skill and follow this loop
unless explicitly overridden.

---

## 1. Issue intake

1. Read the Linear issue **and all comments**.
2. Produce a structured summary:
   - Description
   - Requirements
   - Prerequisites
   - Acceptance criteria
   - Non-goals
3. Tag and link related work in Linear and GitHub:
   - Search for duplicate or related Linear issues.
   - Search GitHub PRs/issues for the same problem or feature.

## 2. Planning and scoping

1. Create a feature branch named from the issue:
   - Format: `feat/linear-<number>-<short-kebab-description>`
   - Example: `feat/linear-123-improve-auth`
2. Define a minimal, bounded scope with explicit success criteria.
3. Identify necessary tests **before** implementation:
   - Unit tests
   - Integration tests
   - Manual/local validation steps

## 3. Implementation

1. Commit in small, focused increments.
2. Include or update tests that cover new behavior.
3. Ensure security and licensing checks are in place.
4. Never commit secrets, tokens, or environment-specific values.

## 4. Verification

1. Run regression tests and new tests locally.
2. If a test fails, diagnose, fix, and re-run before proceeding.
3. Validate endpoints and behavior in a local or staging environment.

## 5. Validation and review

1. Open a PR and link it to the Linear issue.
2. Require code review and approvals before merging.
3. Monitor CI and address failures with transparent commits and explanations.
4. Never claim CI is green without checking it live.

## 6. Deployment readiness

1. Merge only after passing all gates:
   - Tests pass
   - Reviews approve
   - Security scans pass
2. Prepare a canary or limited production verification plan.
3. Do not promise a guaranteed production outcome.

## 7. Production verification

1. Run post-deploy health checks.
2. Validate end-to-end event flow.
3. Establish a rollback plan and monitoring duration.

## 8. Documentation and closure

1. Update the Linear issue with:
   - Final notes
   - Links to PRs
   - Test results
   - Health check outcomes
2. Archive or close the Linear issue if all criteria are satisfied.

---

## Cross-cutting rules

- Always load the related `github` skill for PR mechanics.
- Always load `requesting-code-review` before opening a PR.
- Linear is the source of truth for planning; GitHub is the source of truth for code.
- Use link-only integration between Linear and GitHub (no full bidirectional sync).
- Prefer local/staging verification on Unraid for this homelab project.
