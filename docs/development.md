# Development and maintenance

## Repository map

| Path | Responsibility |
|---|---|
| `app/` | Streamlit pages, shared queries, database connection, safe errors. |
| `parser/` | Vendor and sample-data normalization. |
| `db/` | Generic validated CSV loader and required-field map. |
| `init-db/` | New-database DDL and seed data. |
| `scripts/` | Operational wrappers and orchestration. |
| `demo/` | Synthetic demonstration inputs. |
| `docs/` | User, operator, and maintainer documentation. |

## Safe change sequence

1. Identify the input, normalized CSV, database, and dashboard contracts affected.
2. Preserve stable identifiers and units where semantics have not changed.
3. Update parser mappings and required fields together.
4. Add an explicit migration for existing databases when schema/seed data changes.
5. Update synthetic fixtures and documentation.
6. Run Python/shell syntax checks, Compose validation, dependency audit, and relevant tests.
7. Validate against representative vendor exports outside source control.

## Database changes

Treat `init-db/*.sql` as bootstrap definitions, not migrations. Any released
schema change needs a separately reviewed migration that can be applied to an
existing database and a documented rollback or restore plan.

Avoid weakening foreign keys to make ingestion order easier. Fix orchestration
or input contracts instead.

## Parser changes

Parsers should:

- never modify raw input;
- emit deterministic UTF-8 CSVs with stable headers;
- use configured metric identifiers;
- log enough context to diagnose malformed vendor input;
- distinguish missing optional data from invalid required data;
- avoid embedding patient or sample records in verbose logs.

## Dashboard changes

Keep SQL in `app/queries.py`, use bound parameters, and return dataframes with
stable columns. Use `show_data_error` for recoverable page errors. Never expose
raw database exceptions to users.

## Documentation maintenance

Update documentation in the same change whenever commands, paths, environment
variables, CSV headers, metric semantics, or operational risks change. Run a
relative-link check and search for old project/path names before release.

## Validation commands

```bash
python3 -m compileall -q app db parser
find scripts -name '*.sh' -exec bash -n {} +
./scripts/runtime/compose.sh config --quiet
git diff --check
python -m pip_audit \
  -r app/requirements.txt \
  -r db/requirements.txt \
  -r parser/Illumina_Runs/requirements.txt
```

`compileall` creates ignored bytecode caches. Remove them if a clean working
directory is needed; never commit them.
