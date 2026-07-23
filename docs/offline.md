# Offline operation

IlluQC can operate without internet access after its repository, Docker images,
configuration, and required data have been prepared on a connected computer.
The offline computer must already have Docker and Docker Compose v2 installed.

## 1. Prepare images while online

From the IlluQC repository, build the application images and obtain PostgreSQL:

```bash
./scripts/runtime/compose.sh build parser loader streamlit
docker pull postgres:18
```

Export every image referenced by the resolved Compose configuration:

```bash
docker image save \
  --output illuqc-offline-images.tar \
  $(./scripts/runtime/compose.sh config --images)
```

Prepare these items for transfer:

- the complete IlluQC repository at the same reviewed commit;
- `illuqc-offline-images.tar`;
- required raw sequencing inputs and reference CSV files;
- an IlluQC PostgreSQL backup when preserving an existing database.

Do not distribute the active `.env` file unless the transfer method and
destination are approved for secrets. Prefer creating a new deployment-specific
configuration on the offline computer.

## 2. Transfer the deployment

Transfer the repository, image archive, inputs, and optional backup using the
organization's approved removable media or internal file-transfer process.
Verify checksums when the integrity of transferred artifacts matters.

Example archive checksum:

```bash
shasum -a 256 illuqc-offline-images.tar
```

## 3. Import images offline

On the offline computer:

```bash
docker image load --input illuqc-offline-images.tar
docker image ls
./scripts/runtime/compose.sh config --images
```

All images printed by `config --images` must be present locally.

## 4. Configure offline paths and credentials

Create a private local configuration:

```bash
cp .env.example .env
chmod 600 .env
```

Review every external path in `.env`; paths from the connected preparation
computer may not exist offline. Generate a deployment-specific PostgreSQL
password, for example:

```bash
openssl rand -hex 32
```

Store the generated value as `POSTGRES_PASSWORD` in `.env`. Never commit the
file or paste the secret into documentation or command-line arguments.

Create the configured external directories:

```bash
./illuqc setup
```

## 5. Start without rebuilding or pulling

`illuqc start` includes an image build. For the initial offline startup, use the
preloaded images explicitly:

```bash
./scripts/runtime/compose.sh up -d --no-build db streamlit
```

Confirm service health:

```bash
./illuqc status
./illuqc wait-db
```

The dashboard is normally available at <http://localhost:8501>.

## 6. Run workflows offline

Parser and loader jobs use the locally imported images:

```bash
./illuqc load-lab-data
./illuqc parse R001 "HLA"
./illuqc load R001
./illuqc ingest-samples R001
```

The synthetic demonstration can also be loaded:

```bash
./illuqc demo
```

The demo refreshes the configured processed run and sample directories. Use
demo-specific paths rather than production paths.

## Restore an existing database

Create the backup on the source deployment:

```bash
./illuqc backup
```

Transfer the resulting `.sql.gz` file and restore it offline:

```bash
./illuqc restore /path/to/backup.sql.gz
```

Use compatible IlluQC application and database schema versions. Back up the
offline database before upgrades or image replacement.

## Operations unavailable without prepared artifacts

An isolated deployment cannot perform operations that require internet access,
including:

- pulling missing or updated container images;
- rebuilding layers whose dependencies are not cached locally;
- downloading Python packages;
- updating the vulnerability data used by `pip-audit`;
- retrieving operating-system or base-image security updates.

Build, audit, and export images from the exact reviewed IlluQC commit intended
for the offline deployment. Repeat the controlled transfer process when
updating code, images, or vulnerability fixes.
