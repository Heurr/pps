.PHONY: help
help: # Show help for each of the Makefile recipes
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m: $$(echo $$l | cut -f 2- -d'#')\n"; done

DOCKER_ID ?= price-services-api-1
TA ?= -v tests/

setup-pre-commit: # Setup pre-commit in the current env
	pip3 install pre-commit
	pre-commit install

env: # Enter venv with all dependencies installed
	poetry run pip3 install pre-commit
	poetry run pre-commit install
	poetry shell

build: # Build the app container
	docker compose -f docker-compose.yaml build

up: # Spin up the project
	docker compose -f docker-compose.yaml up

up-d: # Spin up the project in the background
	docker compose -f docker-compose.yaml up -d

down: # Tear down the project
	docker compose -f docker-compose.yaml down

test: # Run tests in project, optionally set DOCKER_ID for docker name and TEST_ARGS for test arguments
	docker exec -it $(DOCKER_ID) pytest $(TA)

test-script: # Run tests using a test script
	docker exec -it $(DOCKER_ID) scripts/tests.sh

bash: # Start an interactive session with the project
	docker exec -it $(DOCKER_ID) bash

lint: # Run the every linting script and a format script
	pre-commit run --all-files
