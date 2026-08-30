# redgreen — common tasks. `make test` and `make smoke` need no API key.
PY ?= python
export PYTHONPATH := src

.PHONY: help test smoke eval eval-no-reviewer report clean

help:
	@echo "make test              run the test suite (no API key)"
	@echo "make smoke             full pipeline on one task, scripted model (no API key)"
	@echo "make eval              baseline vs. agent over all tasks (needs ANTHROPIC_API_KEY)"
	@echo "make eval-no-reviewer  ablation: agent with the Reviewer phase disabled"
	@echo "make clean             remove generated caches and results"

test:
	$(PY) -m pytest

smoke:
	$(PY) -m eval.run --smoke

eval:
	$(PY) -m eval.run

eval-no-reviewer:
	$(PY) -m eval.run --no-reviewer --out results/no_reviewer

clean:
	rm -rf .pytest_cache **/__pycache__ results/smoke results/no_reviewer
