Golden eval set for __AGENT_NAME__.

- [`golden_set.yaml`](golden_set.yaml): planning examples for expected tool use and outcomes.
- [`basic-dataset.json`](../tests/eval/datasets/basic-dataset.json) and
  [`eval_config.yaml`](../tests/eval/eval_config.yaml): two runnable starter cases with
  final-response rubrics, using sample data only. The booking refusal rubric checks what the
  agent says; the wiring test checks that no booking tool is available.
- `thresholds.yaml`: 80% starter pass marks; the business owner (__OWNER__) may propose higher marks.
- `baseline/`: placeholder only. AI Governance must approve real results before they are used.

The `coverage` CI job enforces the 80% starter threshold with `pytest-cov` against `agent/`
and fails closed if the threshold is missing or invalid. The `quality` job runs Ruff, its
complexity check (maximum 10), and ty.

The standalone `.github/workflows/eval_gate.py` compares compatible complete
`agents-cli` result JSON against the approved baseline, the 80% outcome-quality mark and
`max_regression`. It requires a JSON manifest with SHA-256 digests named `dataset_sha256`,
`config_sha256` and `results_sha256`. These link evidence to the dataset, config and baseline;
they do not prove approval. AI Governance must review the baseline and manifest. This helper
currently supports only the starter final-response metric and has not been validated against
live results. It is not wired into CI. The `evals_no_regression` job still fails deliberately.

Run `uv run pytest` for local tests without cloud credentials. Those tests are not model
evaluation. For live evaluation, use the approved non-production project and confirm that
both model inference (not via a Gemini API key) and the managed evaluator are available
in policy-approved regions.
Do not use the CLI's default grading region. In the following command, replace
`APPROVED_EVAL_REGION` with the approved grading region; set the model's inference region
separately with `GOOGLE_CLOUD_LOCATION` as described in the [README](../README.md).

```bash
agents-cli eval run --dataset tests/eval/datasets/basic-dataset.json --config tests/eval/eval_config.yaml --region APPROVED_EVAL_REGION
```

If the managed evaluator is unavailable in an approved region, stop rather than falling
back to an unapproved endpoint. Keep eval artefacts local; they can contain model inputs,
outputs and tool payloads. This sample has no accepted baseline.
A successful sample run is not merge evidence.
