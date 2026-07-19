SHELL := /usr/bin/env bash

ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE ?= docker compose

.PHONY: setup-data-dirs up down reset logs db-shell app \
        parse parse-all parse-multiqc-all parse-sample-metadata-all add-sample-qc-libraries load-reference load load-all load-sample-data load-sample-qc-metrics \
        backup restore wait-for-db demo

setup-data-dirs:
	bash scripts/setup_data_dirs.sh

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
	$(COMPOSE) exec db psql -U "$${POSTGRES_USER:-postgres}" -d "$${POSTGRES_DB:-illuqcdb}"

wait-for-db:
	bash scripts/wait_for_db.sh

parse:
	bash scripts/parse_run.sh "$(RUN_ID)" "$(DESCRIPTION)"

parse-all:
	bash scripts/parse_all_runs.sh

parse-multiqc-all:
	bash scripts/parse_multiqc_all.sh

parse-sample-metadata-all:
	bash scripts/parse_sample_metadata_all.sh

add-sample-qc-libraries:
	bash scripts/add_libraries_to_sample_qc.sh

load-reference:
	bash scripts/load_reference_tables.sh

load:
	bash scripts/load_run.sh "$(RUN_ID)"

load-all:
	bash scripts/load_all_runs.sh

load-sample-data:
	bash scripts/load_sample_data.sh

load-sample-qc-metrics:
	bash scripts/load_sample_qc_metrics.sh

backup:
	bash scripts/backup_db.sh

restore:
	bash scripts/restore_db.sh "$(BACKUP)"

demo:
	bash scripts/load_demo.sh
