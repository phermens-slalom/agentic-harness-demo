# Project site

A static, no-build project site for first-time readers. It lives in [`site/`](../../site) and is published to
GitHub Pages by [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml).

The site summarises the docs. It does not replace them. The delivery lanes and the persona section summarise
[`DELIVERY.md`](../DELIVERY.md) and [`PERSONAS.md`](../PERSONAS.md): the lanes are a proposal and the site says so. Where the two disagree, the roadmap wins, then these
docs, then the site. Fix the site.

## What is in `site/`

| Path | What it is |
|---|---|
| `index.html` | The main page: vision, the two layers (harness and delivery lanes), a persona switcher, how it works, a merge-gate replay, architecture, safety, status and blockers, comparison, getting started, FAQ and sources |
| `roadmap.html` | The roadmap in plain language: what each milestone is worth, the next few steps, what is waiting on people |
| `glossary.html` | The glossary, mirroring [`GLOSSARY.md`](../GLOSSARY.md) with a filter box |
| `assets/css/styles.css` | All styling. Light theme, system fonts, no external requests |
| `assets/js/main.js` | Small, dependency-free: scroll reveal, tabs (architecture views and the persona switcher), copy buttons, the gate replay |
| `assets/img/` | Hand-drawn SVG art: hero scene, four characters, backgrounds, favicon |
| `.nojekyll` | Tells GitHub Pages to serve the folder as it is |

Design choices: no framework, no build step, no third-party scripts, fonts or analytics. Every page works
without JavaScript except the gate replay, the tabs and the copy buttons.

### The gate replay is a replay

The "merge gate" section does not reimplement the gate in the browser. Each scenario is a documented output
of the real code, taken from [`EXAMPLES.md`](../EXAMPLES.md) (examples 2 to 7), from a task in
`evals/golden_tasks/` run through `evals/run_evals.py`, or (reviewer lockout) from the literal reason string in
`merge_gate.py`, which `tests/test_workflow.py` checks. If the gate's rules or outputs change, update the
scenarios in `site/assets/js/main.js` in the same PR.

## Preview locally

```bash
python -m http.server -d site 8000
# open http://localhost:8000
```

## Deploy to GitHub Pages (same repo, no extra repo needed)

The workflow publishes `site/` with the official Pages actions, pinned by commit SHA, with least-privilege
permissions. It runs on a push to `main` that touches `site/**` (or the workflow itself), and on demand.

1. **Open a pull request** from this branch to `main` and get it reviewed. Workflow files are control files in
   this repo, so a person must review `pages.yml`. The workflow only runs from the default branch.
2. **Decide who may see it first.** A Pages site is public on the internet by default, even when the repo is
   private. The site says plainly that the repo is early stage and not yet security reviewed, and it lists open
   questions. Confirm that is acceptable to publish. For private repos, GitHub Pages access control is an
   Enterprise Cloud feature. TODO: verify against GitHub's current Pages documentation.
3. **Enable Pages.** In the repo go to **Settings → Pages → Build and deployment → Source** and choose
   **GitHub Actions**. Nothing else is needed. Pages is not available for private repos on every GitHub plan.
   TODO: verify your plan in GitHub's documentation.
4. **Merge the pull request.** The `pages` workflow starts. Watch it under **Actions → pages**. The `deploy` job
   uses the `github-pages` environment, which by default only allows deployments from `main`.
5. **Open the site.** The URL is printed on the `deploy` job and shown under **Settings → Pages**. For a project
   repo it is `https://<owner>.github.io/<repo>/`.
6. **Redeploy any time** from **Actions → pages → Run workflow**, or by merging another change to `site/`.
7. **Roll back** by reverting the pull request. The next run publishes the previous content.

### If the deployment fails

| Symptom | Likely cause |
|---|---|
| `Get Pages site failed` or `Not Found` | Pages is not enabled yet. Do step 3. |
| `Branch ... is not allowed to deploy to github-pages` | The workflow ran from a branch other than `main`. Merge first, or add the branch to the `github-pages` environment rules. |
| Workflow does not start | The change did not touch `site/**` or the workflow. Use **Run workflow**. |
| The page loads but images or styles 404 | Open the site at the full project URL with the trailing slash. All asset paths are relative. |

### Custom domain (optional)

Add a `CNAME` file inside `site/` containing the domain, then set the domain under **Settings → Pages**.
Do this only once the domain owner and the security team agree. Nothing in the repo names a domain today.

## Keeping the site true

1. Change the docs first. Then change the site to match.
2. Run the checks. `tests/test_site.py` fails when a local link, anchor or asset is missing, when a link into
   the repo points at a path that no longer exists, when anything loads from a third-party host, or when the
   Pages workflow stops being SHA-pinned.
3. Update the figures that were true on 26 November 2026: 265 tests, 65 scored golden tasks (67 in total,
   two documented open gaps), the blockers, the milestone states on `index.html` and `roadmap.html`, and the
   `ARCHITECTURE.md` state marks. `tests/test_site.py` checks the task, gap and required-check counts, that
   `glossary.html` has every term in `GLOSSARY.md`, and that `roadmap.html` has a card for every milestone.
   The test count is not checked: run `uv run pytest -q` and copy it.
4. Keep the honest parts: the early-stage banner, the blockers, the "what the controls do not cover" list, and the
   "to be validated" items (licence, security contact). The site says "to be validated" where the docs say
   `TODO: UNCONFIRMED`, and a test fails if "unconfirmed" appears on the site. Do not remove a limit to make the site
   look better.
5. The glossary page is hand-maintained HTML. Add a new `GLOSSARY.md` term to `glossary.html` in the same PR.
6. Keep Australian English in prose.

The `https://github.com/.../blob/main/...` links assume the repo is `phermens-slalom/agentic-harness-demo`
and the default branch is `main`. If the repo moves or is renamed, search and replace that prefix in
`site/index.html`.

## Sources used for the comparison and facts

Re-read on 26 November 2026 from each project's README and licence file (raw files from `raw.githubusercontent.com`):

- [google/adk-python](https://github.com/google/adk-python): Apache-2.0, "code-first Python framework", built-in evaluation and graph workflows
- [google/agents-cli](https://github.com/google/agents-cli): Apache-2.0, CLI and skills for building, evaluating and deploying agents on Google Cloud
- [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands): MIT, self-hosted control centre for coding agents, optional sandboxing
- [openai/codex](https://github.com/openai/codex): "a coding agent from OpenAI that runs locally on your computer"
- [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action): Claude Code on GitHub PRs and issues, runs on your own runner
- [open-policy-agent/opa](https://github.com/open-policy-agent/opa): general-purpose policy engine, Rego, CNCF graduated, Apache-2.0
- [cedar-policy/cedar](https://github.com/cedar-policy/cedar): authorisation policy language, Apache-2.0
- [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks): MIT, secret detection
- [zizmorcore/zizmor](https://github.com/zizmorcore/zizmor): MIT, static analysis for GitHub Actions and other CI/CD
- [sunglasses-dev/sunglasses](https://github.com/sunglasses-dev/sunglasses): MIT, beta, 1,566 listed patterns, "a confidence floor and not a guarantee"
- [CNCF, "PaC and AI"](https://www.cncf.io/blog/2025/08/12/pac-and-ai/): found by search, not reviewed in full

Pins used by `pages.yml` (tags resolved to commit SHAs with `git ls-remote` on 25 November 2026):
`actions/checkout` v7, `actions/upload-pages-artifact` v5.0.0, `actions/deploy-pages` v5.0.1.

### Checked against external sources (26 November 2026)

The site carries the same list as a [validation log](../../site/index.html#validation), one row per statement with
the page it was checked against. Summary:

- GitHub: the [Copilot cloud agent API guide](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api)
  says the issue-assignment APIs need a user token (a personal access token or a GitHub App user-to-server token).
  The [agent tasks REST reference](https://docs.github.com/en/rest/agent-tasks/agent-tasks) refuses installation
  tokens. This is the R2 blocker. [Copilot with data residency](https://docs.github.com/en/enterprise-cloud@latest/admin/data-residency/github-copilot-with-data-residency) lists the United States and European Union
  only, which supports D-10. The setup-steps, custom-agent, firewall and workflow-approval behaviour is documented.
  GitHub now calls it the Copilot cloud agent.
- Google Cloud: [Model Armor locations](https://docs.cloud.google.com/model-armor/locations) list Melbourne and not
  Sydney; [feature availability](https://docs.cloud.google.com/model-armor/feature-availability-by-region) gives
  three filters in Melbourne with data residency enforced. The
  [generative AI locations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations) list Gemini
  for Sydney and do not list Melbourne. Workload Identity Federation with GitHub Actions OIDC is
  [documented](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines).
- ADK: `ModelArmorPlugin` ships with ADK ([adk.dev](https://adk.dev/integrations/model-armor/)). PyPI has
  `google-adk` 2.15.1, `google-cloud-modelarmor` 0.7.5 and `sunglasses` 0.6.20 (0.6.28 is newer, so 0.6.20 is a pin).
- Upstream READMEs confirm the licences and descriptions in the comparison table. The `agents-cli` README uses
  `uvx google-agents-cli setup`; the `--python 3.13` form is this repo's own pin.
- [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
  (the roadmap reference) exists with that title and date (9 December 2025).
- ADK was cross-checked by installing `google-adk` 2.15.1 (latest) and 2.14.0 (`uv.lock`) in clean environments with
  `google-cloud-modelarmor` 0.7.5: the symbols the adapters use exist on both, `block_on_screening_failure` defaults to
  `True`, and 82 adapter, scanner and workflow tests pass on both.
- [agents.md](https://agents.md), the [C4 model](https://c4model.com/abstractions) and the
  [CNCF article](https://www.cncf.io/blog/2025/08/12/pac-and-ai/) were read and match how the docs use them.
- The `pages.yml` pins resolve to real commits (`actions/checkout` at the pinned commit is 7.0.1), and the Gitleaks
  `v8.30.1` tag exists.

### Still to be validated

- The Gitleaks `v8.30.1` release binary and its SHA-256 (`github.com` release pages are blocked), and the tag
  names behind the `pages.yml` action pins (the commits were checked).
- `github.blog` (the changelog entry cited for Copilot residency in the roadmap references) is not reachable; the
  docs page above covers the same point.

## Image prompts

The site's art is hand-drawn SVG in `site/assets/img/`, so it needs no image tool. The prompts below are for
producing richer raster or 3D art in another session, in the same visual language. Treat any generated image
as a draft: check it for stray text, wrong logos and anything that implies a real organisation or product.

### Shared style block (paste at the start of every prompt)

> Modern, sleek, light and bright flat-vector illustration with soft gradients and gentle depth. Background
> near-white with a faint blue tint (#F8FAFF). Palette: ink navy #0B1B3A, indigo #5B5BF0, sky cyan #19B6E6,
> mint #2FD3A0, soft violet #8B5CF6, warm coral accent #FF7A59, amber #FFB020. Rounded shapes, generous
> whitespace, subtle drop shadows, no outlines, friendly and calm rather than sci-fi. No text, no logos, no
> watermarks.

### Prompts

1. **Hero background (wide, 3200×1800).** Style block, then: "Abstract mesh-gradient background of three large,
   soft, overlapping glows in indigo, cyan and mint on a near-white canvas, with a faint dotted grid fading out
   towards the edges. Leave the left half calm and uncluttered for headline text. Nothing sharp, no objects."
2. **Mascot character sheet.** Style block, then: "Character sheet of four friendly characters on a plain
   light background, same art style: (1) a rounded indigo builder robot with a dark visor face, a small
   antenna and an orange cross-strap harness holding a tiny pull-request card; (2) a violet reviewer robot
   with a magnifying glass showing a green tick; (3) a tall arched gate with three round signal lights
   (green, amber, red) and a calm, steady presence; (4) a person with dark hair and a navy jacket holding a
   large green check badge. Front view, consistent proportions, a soft shadow under each."
3. **Eight stage icons (set).** Style block, then: "A set of eight matching rounded-square app-style icons
   with a soft gradient tile and a simple white glyph each: target (frame), ID card (register), cloud
   (provision), plug (connect), code brackets (build), shield with tick (verify), paper plane (release), pulse
   line (operate). Consistent stroke weight, even spacing, transparent background."
4. **Isometric architecture scene.** Style block, then: "Isometric illustration of a small campus of floating
   tiles joined by thin glowing paths: a central tile labelled only by an arch-shaped gate, around it a tile
   of stacked YAML-style document sheets (policy), a tile with a flask (evals), a tile with a template
   blueprint (agent template), and a tile with a terminal window (CLI). Tiny robot and person figures stand
   on separate tiles. Calm, airy, lots of white space."
5. **Section headers (four, 1600×600).** Style block, then one scene each: "(a) vision: a small robot and a
   person walking side by side towards a bright horizon; (b) the gate: the arch gate with a stream of small
   pull-request cards approaching, most passing through a green light and one stopped by amber; (c) safety: a
   large soft shield made of overlapping translucent layers with tiny check marks; (d) status: three stepping
   platforms, solid, dashed and ghosted, with a robot standing on the first."
6. **Social card (1200×630).** Style block, then: "Wide composition with the builder robot at left, the arch
   gate in the centre and the person with a green check at right, a soft mint-to-indigo gradient glow
   behind. Leave a clear empty band along the bottom third for a title to be added later."
7. **Soft loop animation (for a video or Lottie).** Style block, then: "Seamless 6-second loop: small
   pull-request cards glide left to right along a dotted path, the gate's lights cycle green, amber, red, a
   green check pulses above the person. Slow, smooth easing, no camera movement."

**Negative prompt (if the tool supports one):** photorealistic, dark mode, neon cyberpunk, glitch effects,
text, letters, logos, watermarks, humanoid faces with uncanny detail, clutter, harsh shadows.

**Tips.** Generate the characters first (prompt 2), then pass that image as a reference for every later
prompt so the cast stays consistent. Export SVG where the tool allows it; otherwise export PNG at 2× and keep
the file under about 300 KB per image so the page stays fast.
