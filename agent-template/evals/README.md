Golden eval set for __AGENT_NAME__.

- [`golden_set.yaml`](golden_set.yaml): planning examples for expected tool use and outcomes.
- [`basic-dataset.json`](../tests/eval/datasets/basic-dataset.json) and
  [`eval_config.yaml`](../tests/eval/eval_config.yaml): two runnable starter cases with
  final-response rubrics, using sample data only. The booking refusal rubric checks what the
  agent says; the wiring test checks that no booking tool is available.
- `thresholds.yaml`: pass marks. Defined by the business owner (__OWNER__), not by the harness.
- `baseline/`: last accepted results. A PR may not regress against it. Do not edit by hand.

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
outputs and tool payloads. This sample has no accepted baseline or owner-approved threshold.
A successful sample run is not merge evidence.
