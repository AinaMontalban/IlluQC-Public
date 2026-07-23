SHELL := /usr/bin/env bash

ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE ?= bash scripts/runtime/compose.sh

.PHONY: setup-data-dirs up down reset logs db-shell app audit \
        parse parse-thermofisher parse-thermofisher-all parse-illumina-runs parse-all validate-samples prepare-samples load-samples ingest-samples validate-sample prepare-sample load-sample ingest-sample prepare-samples-all load-samples-all parse-sample load-lab-data load-reference load load-runs load-all load-sample-data load-sample-qc-metrics \
        backup restore wait-for-db demo

setup-data-dirs:
	bash scripts/runtime/setup_data_directories.sh

up:
	$(COMPOSE) up --build

app:
	$(COMPOSE) up --build streamlit

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

db-shell:
	$(COMPOSE) exec db psql -U "$${POSTGRES_USER:-illuqc}" -d "$${POSTGRES_DB:-illuqcdb}"

audit:
	python -m pip_audit -r app/requirements.txt -r db/requirements.txt -r parser/Illumina_Runs/requirements.txt

wait-for-db:
	bash scripts/runtime/wait_for_database.sh

parse:
	bash scripts/runs/parse_illumina_run.sh "$(RUN_ID)" "$(DESCRIPTION)"

parse-thermofisher:
	bash scripts/runs/parse_thermofisher_run.sh "$(JSON_FILE)" "$(DESCRIPTION)" "$(MODEL)"

parse-thermofisher-all:
	bash scripts/runs/parse_thermofisher_runs.sh "$(DESCRIPTION)" "$(MODEL)"

parse-illumina-runs:
	bash scripts/runs/parse_illumina_runs.sh

parse-all:
	@echo "WARNING: 'make parse-all' is deprecated; use 'make parse-illumina-runs'." >&2
	bash scripts/runs/parse_illumina_runs.sh

parse-sample:
	@echo "WARNING: 'make parse-sample' is deprecated; use 'make prepare-sample'." >&2
	bash scripts/samples/prepare_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)" "$(FORCE)"

validate-samples:
	bash scripts/samples/validate_run_samples.sh "$(RUN_ID)"

prepare-samples:
	bash scripts/samples/prepare_run_samples.sh "$(RUN_ID)" "" "$(FORCE)"

load-samples:
	bash scripts/samples/load_run_samples.sh "$(RUN_ID)"

ingest-samples:
	bash scripts/samples/prepare_run_samples.sh "$(RUN_ID)" "" "$(FORCE)"
	bash scripts/samples/load_run_samples.sh "$(RUN_ID)"

validate-sample:
	bash scripts/samples/validate_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)"

prepare-sample:
	bash scripts/samples/prepare_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)" "$(FORCE)"

load-sample:
	bash scripts/samples/load_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)"

ingest-sample:
	bash scripts/samples/prepare_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)" "$(FORCE)"
	bash scripts/samples/load_run_samples.sh "$(RUN_ID)" "$(SAMPLE_ID)"

prepare-samples-all:
	bash scripts/samples/prepare_all_run_samples.sh "$(FORCE)"

load-samples-all:
	bash scripts/samples/load_all_run_samples.sh

load-lab-data:
	bash scripts/lab/load_lab_data.sh

load-reference:
	@echo "WARNING: 'make load-reference' is deprecated; use 'make load-lab-data'." >&2
	bash scripts/lab/load_lab_data.sh

load:
	bash scripts/runs/load_run.sh "$(RUN_ID)"

load-runs:
	bash scripts/runs/load_runs.sh

load-all:
	@echo "WARNING: 'make load-all' is deprecated; use 'make load-runs'." >&2
	bash scripts/runs/load_runs.sh

load-sample-data:
	bash scripts/legacy/load_sample_data.sh

load-sample-qc-metrics:
	bash scripts/legacy/load_sample_qc_metrics.sh

backup:
	bash scripts/database/backup_database.sh

restore:
	bash scripts/database/restore_database.sh "$(BACKUP)"

demo:
	bash scripts/database/load_demo_data.sh
