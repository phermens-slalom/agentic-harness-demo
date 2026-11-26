# Technical docs

How individual parts of the harness are built and operated. For the project as a whole (vision, architecture,
decisions, roadmap), see the [documentation index](../README.md).

| Document | What it covers |
|---|---|
| [Input guard](INPUT_GUARD.md) | How untrusted text is scanned before a model reads it: Model Armor, Sunglasses, the composite scanner, shadow mode, the guarded surfaces and the adversarial evals |
| [ADK port notes](ADK_PORT.md) | How the LLM adapters work today (structured output, runners, residency, repo context, skills), and notes for porting to an ADK 2.0 Workflow |
| [Project site](SITE.md) | The static GitHub Pages site: what it holds, how to deploy and update it, and its sources |

## What goes here

- A document goes here when it explains how one component or part is built, wired or operated, and a
  reader would only need it when working on that part.
- A document stays in [`docs/`](../README.md) when it is about the project as a whole: what it is for, how it is
  organised, what was decided, what is open, and how to use or contribute to it.
- Keep the same rules as the other docs: plain English, facts only, and **TODO: UNCONFIRMED** for anything the repo
  does not confirm. Link to the roadmap rather than copying it.
