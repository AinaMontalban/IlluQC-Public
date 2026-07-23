# Dashboard guide

## Pages

- **Activity Summary**: run and sample counts, protocol distribution,
  instrument distribution, repeated samples, and registration dates.
- **Protocols**: metrics and chemistry grouped by run description/protocol.
- **Runs**: detailed run metadata and platform-relevant run QC metrics.
- **Samples**: sample-level metrics across one or more runs.
- **Libraries**: library definitions and sample-metric distributions by library.
- **Lab Data**: instruments, chemistry, libraries, and metric definitions.
- **About**: IlluQC application and database schema versions.

## Database access

`app/db.py` creates one cached SQLAlchemy engine. It validates connectivity with
`SELECT 1`. Credentials are assembled with SQLAlchemy's structured URL API, so
reserved characters in passwords are handled safely.

Queries are centralized in `app/queries.py` and use bound parameters for
filters. Pages should not display exception text directly; use
`app/errors.py:show_data_error` to log details and show a safe message.

## Metric labels and filtering

The dashboard derives user-facing labels from `display_label`, falling back to
`metric_name` and then `metric_id`. Platform metadata in
`qc_metric_definitions` limits metrics to the relevant instrument platform.

## Interpretation

Dashboard values are descriptive. IlluQC does not encode universal pass/fail
criteria. Each laboratory must document local thresholds, version them, and
validate that parser units match source reports.

Missing charts may indicate absent data, an empty selection, unresolved
reference identifiers, or a parser/loader failure. Check database row counts
and logs before interpreting absence as a biological or instrument result.

## Exposure

The Compose configuration publishes Streamlit on all host interfaces unless
the host firewall restricts it. IlluQC currently has no built-in user
authentication or authorization. Place it behind an authenticated reverse
proxy or private network for any non-public data.
