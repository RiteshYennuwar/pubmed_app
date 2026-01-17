.PHONY: setup install dev

setup: 
	python -m venv venv
	@echo "Run: source venv/bin/activate"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"