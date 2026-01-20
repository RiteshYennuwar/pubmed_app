.PHONY: setup install dev

setup: 
	python -m venv venv
	@echo "Run: source venv/bin/activate"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

db:
	pubmed db init

etl:
ifndef TOPIC
	@echo "Error: TOPIC is required"
	@echo "Usage: make etl TOPIC=\"machine learning medicine\""
	@exit 1
endif
	pubmed etl --topic "$(TOPIC)" --max-results $(or $(MAX),100)
	
run:
	pubmed serve