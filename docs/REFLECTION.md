# Reflection: What Building ConsultAI Actually Taught Me

Ryan Good | Organizational Behavior

Building ConsultAI wasn't really about the code. It was about figuring out, hands-on, what
actually happens to a job and the people in it once you take the routine part of the work away
from a person and hand it to a system with guardrails. Here's what I actually learned from
doing it, not just what I'd guess if I hadn't built anything.

## What changes about how the work gets done

Before this, an associate consultant doing a financial diagnosis would pull the numbers
themselves, calculate every ratio by hand, read through everything, and write up a first draft
-- hours of work before any real thinking happens. ConsultAI compresses that down to minutes:
upload a statement, the system validates it, calculates the real metrics, flags what's worth
caring about, and drafts an interpretation. But the part that actually matters for this class
isn't the speed -- it's that I had to design, on purpose, exactly where the automation stops
and a person has to step back in.

That's not a small design choice. It's the whole point. I built a system where the AI can
compute, flag, and draft, but it **cannot** approve its own work, send anything externally, or
get treated as final without a named human -- specifically someone with manager-level authority
-- signing off. I tested that boundary for real, not just described it: I tried to get the
system to approve something as an "associate" and it refused, every time, with a specific
error. That refusal is the actual evidence that a control works, not just a sentence in a
report saying it should.

## Structure, culture, teamwork, decision rights

**Structure** shifts the associate's job from *producing* information to *owning the quality*
of information someone else (or something else) produced. That's a real change in what the
role is for. **Culture** shifts toward evidence -- every claim in the system has to trace back
to an actual number, which is a good habit, but it also creates a real risk of people trusting
a confident-looking AI output without checking it, which is exactly why I built the claim
verification step that flags anything unsupported instead of letting it through quietly.
**Teamwork** changes in a way I didn't expect until I built it: when a validation blocks a bad
run, or a finding comes back unverified, there's now an actual escalation point and a specific
person responsible for it, instead of a vague "someone should catch that." **Decision rights**
stay clear on purpose -- the system drafts, the associate checks, the manager decides. I made
sure there's no path, anywhere in the code, where the AI's own output can trigger an approval.
That was a deliberate choice, not an accident.

## What this means for me

The instructions for this assignment are blunt about it: "I will do more work" isn't a real
answer. After actually building this, I don't think the honest answer is "I'd do more
analysis faster" either. It's that I'd move toward owning the *process itself* -- the
validation rules, the thresholds, the review protocol -- across a whole team's cases, not just
my own. That's a genuinely different kind of value than being fast at one task. I'd also be the
person who notices when something breaks in a pattern (two similar failures, say) and actually
changes the workflow because of it, instead of just fixing the one instance and moving on.

## What I'd push back on, honestly

I don't want to oversell this. Building it also showed me real risks worth naming: if an
associate stops doing the manual calculations, they might never build the instinct to catch a
wrong number by eye. The system trusts whoever types "manager" into a role field -- it doesn't
verify identity, which would be a real gap in an actual deployment. And the detection
thresholds I picked (like a 3-point margin drop) are reasonable defaults, not something I've
validated against how real, experienced consultants actually judge significance. None of that
makes the system useless -- it just means the human part of this isn't optional polish, it's
load-bearing.

## Where this lands

I automated the routine part of the job. I built a failure protocol and actually tested it
against real bad data and a real attempt to manipulate the AI, not just described what should
happen. And doing that work is exactly what convinced me the higher-value role isn't "do the
same job faster" -- it's becoming the person who owns whether the automated process can
actually be trusted, which turns out to be a much bigger and more interesting job than the one
it replaced.

**AI disclosure:** Claude (Anthropic API) was used for the application's own analysis features
and, with Claude Code, to help build and test the application itself.
