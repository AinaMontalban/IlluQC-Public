# IlluQC documentation

This documentation describes the current IlluQC implementation: its containers,
data contracts, supported ingestion paths, dashboard, and operational model.

## Start here

- [Getting started](getting-started.md): first installation and a complete first run.
- [Architecture](architecture.md): components, boundaries, and data flow.
- [Configuration](configuration.md): every supported environment variable and mount.
- [Workflows](workflows.md): Illumina, Thermo Fisher, MultiQC, metadata, and loading.
- [Data model](data-model.md): PostgreSQL tables, keys, relationships, and CSV contracts.
- [Dashboard](dashboard.md): pages, queries, filters, and interpretation boundaries.
- [Operations](operations.md): startup, health, logs, backup, restore, and upgrades.
- [Deployment](deployment.md): Docker Compose, native Python, and Apptainer/Singularity.
- [Security](security.md): secrets, network exposure, filesystem permissions, and sensitive data.
- [Troubleshooting](troubleshooting.md): symptoms, diagnostics, and recovery procedures.
- [Development](development.md): repository conventions and safe extension points.
- [Demo data](../demo/README.md): synthetic MiSeq, chemistry, run, and repeated-sample fixtures.

## Scope and intended use

IlluQC aggregates sequencing quality-control metadata for operational review and
research. It does not prescribe acceptance thresholds and is not a diagnostic
medical device. Laboratories are responsible for validating supported input
formats, metric interpretation, access controls, and upgrade procedures in
their own environment.

## Documentation conventions

Commands assume the repository root as the working directory. Host paths use
the defaults from `.env.example`; configured paths always take precedence.
`RUN_ID` and similar uppercase values are placeholders.
