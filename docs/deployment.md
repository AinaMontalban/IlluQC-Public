# Deployment options

## Docker Compose

Docker Compose is the reference deployment. It provides service health checks,
consistent dependency versions, read-only raw-data mounts, durable PostgreSQL
storage, and short-lived parser/loader jobs.

IlluQC routes Compose operations through `scripts/runtime/compose.sh` and
requires Docker Compose v2.

```bash
cp .env.example .env
./illuqc setup
./illuqc config
./illuqc start
```

Use a reverse proxy for TLS and authentication. Do not publish PostgreSQL unless
external database access is explicitly required and firewalled.

## Native Python

Native use requires Python 3.11, PostgreSQL/client tools, and component
dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
python -m pip install -r db/requirements.txt
python -m pip install -r parser/Illumina_Runs/requirements.txt
```

Export `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` before
starting Streamlit. The Make parser/loader wrappers are Compose-oriented; call
their Python entry points directly for a fully native workflow.

## Apptainer/Singularity

Build OCI images on a Docker-capable machine, convert them to SIF, then bind the
same raw, processed, configuration, and log paths. Run PostgreSQL as an external
managed service rather than inside an unprivileged application image.

Pass individual `DB_*` variables into the Streamlit container. Avoid embedding
passwords in SIF files, job scripts, or shared shell history; use the cluster's
approved secret mechanism.

See [INSTALLATION_OPTIONS.md](../INSTALLATION_OPTIONS.md) for concrete commands.

## Production checklist

- immutable, reviewed image tag selected;
- external paths are absolute and backed up appropriately;
- PostgreSQL storage is durable and monitored;
- database password is deployment-specific;
- Streamlit is behind authentication and TLS;
- containers run as a non-root UID/GID;
- raw data mounts are read-only;
- backups have been test-restored;
- supported vendor formats have been locally validated;
- dependency audit and organizational vulnerability scanning are complete;
- recovery and rollback owners are identified.
