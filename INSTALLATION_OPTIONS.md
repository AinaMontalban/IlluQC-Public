# IlluQC installation options

IlluQC can be installed in three ways:

1. Native Python and PostgreSQL
2. Docker Compose
3. Apptainer or Singularity

Docker Compose is the simplest option for a local workstation. Native
installation is useful for development or a managed server. Apptainer is
intended for HPC environments where Docker is unavailable.

## Shared configuration and data layout

Clone the repository and create a local configuration:

```bash
git clone <repository-url> IlluQC
cd IlluQC
cp .env.example .env
```

Review `.env`, particularly these paths:

```dotenv
ILLUMINA_RAW_DATA_DIR=../NGS_Data/raw_data/illumina
THERMOFISHER_RAW_DATA_DIR=../NGS_Data/raw_data/thermofisher
PROCESSED_DATA_DIR=../NGS_Data/processed
LOG_DIR=../NGS_Data/logs
BACKUP_DIR=../NGS_Data/backups
POSTGRES_DATA_DIR=../NGS_Data/postgres_data
CONFIG_DIR=../NGS_Data/config
```

Create the external directories:

```bash
./illuqc setup
```

Raw data and generated data remain outside the repository:

```text
NGS_Data/
├── raw_data/
│   ├── illumina/
│   │   └── RUN_ID/
│   └── thermofisher/
│       ├── serialized_*.json
│       └── Plan_*.json
├── processed/
│   ├── Runs_Data/
│   └── Samples_Data/
├── logs/
├── backups/
├── postgres_data/
└── config/
```

## Option 1: native installation

### Requirements

- Python 3.11
- PostgreSQL and its client tools
- A compiler if binary Python packages are unavailable for the host

Create a Python environment and install the component dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r app/requirements.txt
python -m pip install -r parser/Illumina_Runs/requirements.txt
python -m pip install -r requirements-dev.txt
```

The Thermo Fisher parser uses the Python standard library and needs no extra
Python packages.

Audit pinned runtime dependencies before releases or deployments:

```bash
./illuqc audit
```

Configure a PostgreSQL server reachable from the host. For example:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=illuqcdb
POSTGRES_USER=illuqc
POSTGRES_PASSWORD=replace-with-a-long-random-password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=illuqcdb
DB_USER=illuqc
DB_PASSWORD=replace-this-password
```

Create the database according to the local PostgreSQL administration policy,
then initialize it:

```bash
set -a
source .env
set +a

psql --host "$POSTGRES_HOST" --port "$POSTGRES_PORT" \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --file init-db/01_schema_ddl.sql

psql --host "$POSTGRES_HOST" --port "$POSTGRES_PORT" \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --file init-db/02_schema_seed.sql
```

Start the dashboard:

```bash
streamlit run app/IlluQC_app.py --server.port 8501
```

Open <http://localhost:8501>.

Run parsers directly in the native environment. Examples:

```bash
python parser/Illumina_Runs/Illumina_sequencing_data_parser.py \
  --run-folder "$ILLUMINA_RAW_DATA_DIR/RUN_ID" \
  --output-dir "$PROCESSED_DATA_DIR/Runs_Data" \
  --run-description "Run description"

python parser/Thermofisher_Data/ThermoFisher_sequencing_data_parser.py \
  --json-file "$THERMOFISHER_RAW_DATA_DIR/serialized_run.json" \
  --instrument-model S5 \
  --output-dir "$PROCESSED_DATA_DIR/Runs_Data"
```

The `illuqc parse*` commands execute parsers through Docker Compose. Use the
direct Python commands above on a fully native installation.

## Option 2: Docker Compose

### Requirements

- Docker Desktop, or Docker Engine with the Compose plugin

Prepare configuration and start the services:

```bash
cp .env.example .env
./illuqc setup
./illuqc start
```

On Linux, set `LOCAL_UID` and `LOCAL_GID` in `.env` to the output of `id -u`
and `id -g` so bind-mounted output remains owned by your host account.

Open <http://localhost:8501>. Confirm service status with:

```bash
./illuqc status
./illuqc logs streamlit
```

Common operations:

```bash
# Illumina
./illuqc parse RUN_ID "Run description"

# One Thermo Fisher export
./illuqc parse-thermofisher serialized_run.json S5 "Run description"

# Every S5 export
./illuqc parse-thermofisher-all S5

# Every Genexus export
./illuqc parse-thermofisher-all GENEXUS

# Load normalized output
./illuqc load RUN_ID
```

Stop services without deleting PostgreSQL data:

```bash
./illuqc stop
```

Do not run `docker compose down -v` on a database that must be preserved.

## Option 3: Apptainer or Singularity

### Requirements

- Apptainer 1.2 or newer, or a compatible Singularity installation
- Access to a PostgreSQL server from the execution node
- Docker on a separate build machine, or access to published OCI images

Apptainer normally runs PostgreSQL as an external managed service. Do not place
the live PostgreSQL data directory inside an unprivileged application image.

### Build images from the local Docker images

On a machine with Docker and Apptainer:

```bash
./scripts/runtime/compose.sh build parser streamlit loader

apptainer build illuqc-parser.sif \
  docker-daemon://illuqc_parser:0.1.0
apptainer build illuqc-loader.sif \
  docker-daemon://illuqc_loader:0.1.0
apptainer build illuqc-streamlit.sif \
  docker-daemon://illuqc_streamlit:0.1.0
```

Image names use `PROJECT_NAME` from `.env`. Adjust the source names if a
different project name is configured. Copy the resulting `.sif` files to the
cluster.

### Run the dashboard

```bash
set -a
source .env
set +a

apptainer exec \
  --cleanenv \
  --env "DB_HOST=${POSTGRES_HOST}" \
  --env "DB_PORT=${POSTGRES_PORT}" \
  --env "DB_NAME=${POSTGRES_DB}" \
  --env "DB_USER=${POSTGRES_USER}" \
  --env "DB_PASSWORD=${POSTGRES_PASSWORD}" \
  --env STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  --env STREAMLIT_SERVER_PORT=8501 \
  --bind "$CONFIG_DIR:/config:ro" \
  --bind "$LOG_DIR:/logs" \
  illuqc-streamlit.sif \
  streamlit run /opt/illuqc/app/IlluQC_app.py \
    --server.address=0.0.0.0 --server.port=8501
```

Use a scheduler job and SSH tunnel when compute nodes are not directly
reachable:

```bash
ssh -N -L 8501:COMPUTE_NODE:8501 USER@CLUSTER_LOGIN_HOST
```

Then open <http://localhost:8501>.

### Run an Illumina parser

```bash
apptainer exec \
  --cleanenv \
  --bind "$ILLUMINA_RAW_DATA_DIR:/data/raw/illumina:ro" \
  --bind "$PROCESSED_DATA_DIR:/data/processed" \
  --bind "$LOG_DIR:/logs" \
  illuqc-parser.sif \
  python /opt/illuqc/parser/Illumina_Runs/Illumina_sequencing_data_parser.py \
    --run-folder /data/raw/illumina/RUN_ID \
    --output-dir /data/processed/Runs_Data \
    --run-description "Run description"
```

### Run a Thermo Fisher parser

```bash
apptainer exec \
  --cleanenv \
  --bind "$THERMOFISHER_RAW_DATA_DIR:/data/raw/thermofisher:ro" \
  --bind "$PROCESSED_DATA_DIR:/data/processed" \
  --bind "$LOG_DIR:/logs" \
  illuqc-parser.sif \
  python /opt/illuqc/parser/Thermofisher_Data/ThermoFisher_sequencing_data_parser.py \
    --json-file /data/raw/thermofisher/serialized_run.json \
    --instrument-model S5 \
    --output-dir /data/processed/Runs_Data
```

Replace `apptainer` with `singularity` when that is the command provided by the
cluster.

## Choosing an installation method

| Requirement | Native | Docker Compose | Apptainer |
|---|---:|---:|---:|
| Easiest local setup |  | ✓ |  |
| Direct Python development | ✓ |  |  |
| Bundled PostgreSQL |  | ✓ |  |
| HPC without Docker |  |  | ✓ |
| Managed external PostgreSQL | ✓ | ✓ | ✓ |
| Reproducible packaged dependencies |  | ✓ | ✓ |

Regardless of the method, back up PostgreSQL before upgrades and never commit
raw sequencing data, credentials, database storage, or patient information.
