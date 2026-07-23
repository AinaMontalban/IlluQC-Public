# Security guidance

## Threat model

IlluQC processes laboratory metadata that may include sample identifiers and
operational details. Protect confidentiality and integrity at the host,
container, database, network, backup, and log layers.

## Credentials

- Generate a unique PostgreSQL password for each deployment.
- Keep `.env` untracked and readable only by the service owner (`chmod 600 .env`).
- Never pass passwords through loader command-line arguments; they may appear in
  process listings or audit logs.
- Do not commit `.env`, database dumps, Streamlit secrets, or production logs.
- Prefer an institutional secret manager for orchestrated deployments.
- Rotate credentials through a planned database-role change; changing `.env`
  alone does not change an existing PostgreSQL password.
- The loader accepts its password only through `POSTGRES_PASSWORD`; it has no
  password command-line option.

## Network controls

PostgreSQL is not published by the default Compose file. Preserve that boundary
unless remote access is required. Streamlit is published on the configured host
port and has no built-in IlluQC authentication. Restrict it with a firewall,
VPN/private network, or authenticated TLS reverse proxy.

## Filesystem controls

- Raw inputs are mounted read-only into the parser.
- The loader sees processed output read-only.
- Run containers as a non-root UID/GID matching host ownership where suitable.
- Restrict `POSTGRES_DATA_DIR`, `BACKUP_DIR`, `CONFIG_DIR`, and logs to authorized
  operators.
- Encrypt disks and backups according to institutional policy.

## Application errors and logs

The dashboard shows sanitized errors and records details in service logs. Treat
logs as potentially sensitive because they can contain identifiers and paths.
Do not log database passwords, connection URLs containing credentials, or raw
records unnecessarily.

## Supply chain

Runtime Python dependencies and base-image versions are pinned. Run:

```bash
python -m pip install -r requirements-dev.txt
illuqc audit
```

Also scan built container images with the organization's approved scanner.
Review findings in context, rebuild when patched dependencies become available,
and record risk acceptance where immediate remediation is impossible.

## Data governance

Use synthetic data for demonstrations. Establish retention and deletion rules
for raw inputs, normalized CSVs, database rows, logs, and backups. IlluQC does
not implement record-level authorization, consent management, or automatic
retention enforcement.
