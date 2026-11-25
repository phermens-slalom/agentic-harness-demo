# Thin wrappers over scripts/e2e.py (the logic lives there so Windows, macOS and Linux behave the same).
# Windows without make: use `.\scripts\e2e.ps1` instead.
PYTHON ?= python

.PHONY: e2e e2e-keep e2e-live clean clean-artefacts clean-e2e clean-files

e2e:              ## full workflow, then delete the generated agent
	$(PYTHON) scripts/e2e.py

e2e-keep:         ## same, but leave the agent in .e2e-work/ for inspection
	$(PYTHON) scripts/e2e.py --keep

e2e-live:         ## also run live evals (needs approved credentials and HARNESS_EVAL_REGION)
	$(PYTHON) scripts/e2e.py --live-evals

clean:            ## clean all generated files and directories
	$(MAKE) clean-artefacts
	$(MAKE) clean-e2e
	$(MAKE) clean-files

clean-artefacts:  ## clean build artefacts and generated agent
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('build', 'dist', 'my-agent')]"

clean-e2e:        ## clean end-to-end work and report directories
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('.e2e-work', 'e2e-report')]"

clean-files:      ## clean evaluation report files
	$(PYTHON) -c "import os; [os.remove(p) for p in ('eval_report.json', 'harness-eval-report.json') if os.path.exists(p)]"
