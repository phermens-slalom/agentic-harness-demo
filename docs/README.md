# Documentation index

Start here. Pick the path that matches why you are reading.

## Reading paths

| You are... | Read in this order |
|---|---|
| New and want the big picture | [Vision](VISION.md) → [Delivery process](DELIVERY.md) → [Examples](EXAMPLES.md) → [Glossary](GLOSSARY.md) |
| A developer who wants to run it | [Getting started](GETTING_STARTED.md) → [Architecture](ARCHITECTURE.md) → [Contributing](CONTRIBUTING.md) |
| A reviewer or approver | [Vision](VISION.md) → [Personas](PERSONAS.md) → [Security](SECURITY.md) → [Decisions](DECISIONS.md) → [Open questions](OPEN_QUESTIONS.md) |
| Looking for what is done and what is next | [Roadmap](ROADMAP.md) → [Changelog](CHANGELOG.md) → [Open questions](OPEN_QUESTIONS.md) |
| Stuck | [FAQ](FAQ.md) |
| Publishing or updating the project site, or changing the adapters or the input guard | [Technical docs](tech/README.md) |

## Project docs

Broad documents about the project as a whole. They live in this folder.

| Document | What it is |
|---|---|
| [Vision](VISION.md) | The short summary: what the repo is for and what each folder holds |
| [Delivery process](DELIVERY.md) | The proposed lanes from idea to production, their exit requirements and what enforces them, a proposed lane-aware RACI, reliability and standards |
| [Personas](PERSONAS.md) | Who works in which lane, how they come in, and what they raise or approve |
| [Architecture](ARCHITECTURE.md) | A technical breakdown in three levels (context, containers, components) |
| [Examples](EXAMPLES.md) | Worked examples using insurance metaphors |
| [Glossary](GLOSSARY.md) | Acronyms, roles, terms and roadmap codes in plain English |
| [Getting started](GETTING_STARTED.md) | Install, run, test and try the bootstrap |
| [Contributing](CONTRIBUTING.md) | How to change this repo safely, and how work is recorded as done |
| [Security](SECURITY.md) | The controls in place, what they do not cover, and known gaps |
| [Decisions](DECISIONS.md) | The design decisions in plain English, with their status |
| [Open questions](OPEN_QUESTIONS.md) | What is blocked or unknown, and who owns the answer |
| [FAQ](FAQ.md) | Common questions and fixes |
| [Changelog](CHANGELOG.md) | What changed, by date, and the design choices behind the first version |
| [Roadmap](ROADMAP.md) | The full backlog, decisions, acceptance criteria and work log (the source of truth) |

## Technical docs

How individual parts are built and operated. They live in [`tech/`](tech/README.md).

| Document | What it is |
|---|---|
| [Input guard](tech/INPUT_GUARD.md) | How untrusted text is scanned: Model Armor, Sunglasses, the composite, shadow mode and the adversarial evals |
| [ADK port notes](tech/ADK_PORT.md) | How the LLM adapters work today, and notes for the ADK 2.0 port |
| [Project site](tech/SITE.md) | The static GitHub Pages site: what it holds, how to deploy and update it, sources, image prompts |

## Rules for these docs

- Plain, short English. Facts only. Nothing here describes a feature that is not in the repo or the roadmap.
- Anything the repo does not confirm is marked **TODO: UNCONFIRMED**.
- The [Roadmap](ROADMAP.md) wins if a document here disagrees with it. Fix the document.
- Update the directly related document in the same PR as a behaviour change.
- Project docs stay in this folder. Documents about how one part is built or operated go in `tech/`.

## Licence

TODO: UNCONFIRMED. No licence file is in the repo. Do not assume one.
