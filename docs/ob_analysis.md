# Organizational Behavior Analysis — ConsultAI

## Six dimensions

**Culture.** Shifts toward experimentation and evidence-based review — every claim must cite a
source. Risk: automation bias (trusting a confident-sounding draft) and skill atrophy in
junior staff who no longer build every model by hand. Mitigation: verification norms (the
claim-verification step is mandatory, not optional) and preserved manual-modeling training.

**Communication.** Findings arrive in a standardized, cited format, which speeds handoffs but
reduces the informal back-and-forth where junior analysts used to ask "does this number look
right?" out loud. Mitigation: a visible question/escalation log and required review comments.

**Structure.** The associate's role shifts from manually compiling data to owning the quality
of AI-assisted output — reviewing citations, challenging conclusions, and deciding what gets
escalated. The manager keeps final approval authority but takes on an added quality-control
responsibility.

**Coordination.** Run IDs, linked reruns, and the audit trail make handoffs between associate
and manager traceable in a way that an email thread or shared doc usually isn't — reducing
duplicated work and "which version is current" confusion.

**Workflow.** Manual research → calculation → draft becomes: deterministic validation → Python
metrics → AI-drafted hypotheses → human verification → manager approval. The sequence is
shorter but adds an explicit verification gate that didn't exist before.

**Decision rights.** The system computes and drafts; the associate checks; the manager
authorizes. Client-facing decisions stay entirely human — the system has no path to send
anything externally, by design.

## The higher-value role (not "I will do more work")

**Proposed role: AI-enabled consulting workstream lead.** Rather than simply producing more
briefings faster, the associate who adopts ConsultAI should:

- Own analytical quality and issue-prioritization standards for the team, not just one case.
- Design and audit reusable validation/scoring logic so other associates inherit a tested process.
- Coach newer analysts on reading AI output critically rather than trusting it by default.
- Translate verified evidence into client-relevant strategic options for the manager.
- Own escalation handling across cases — the person who notices when a failure pattern
  repeats and changes the workflow (per `manager_protocol.md`'s repeated-failure rules).

## Risks to name explicitly

- **Overreliance:** a plausible-sounding AI draft can be wrong in ways that are hard to spot
  without discipline — this is why claim verification is a hard gate, not a suggestion.
- **Weaker junior training:** if associates stop doing the arithmetic by hand, they may never
  build the intuition to catch a wrong number. Recommendation: keep a manual-calculation
  exercise in new-analyst onboarding even after this tool is adopted.
- **Unclear accountability:** without a named decision owner, "the AI said so" can become an
  excuse. This is why the protocol requires a reviewer name, role, and reason on every decision.
- **Review-time squeeze:** if managers expect faster output without allocating real review
  time, the human-in-the-loop gate becomes theater. The protocol's repeated-failure escalation
  (e.g., mandatory second-analyst verification) is partly a safeguard against this.
