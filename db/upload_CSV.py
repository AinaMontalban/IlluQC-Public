#!/usr/bin/env python3
"""Utility to load a CSV file into a PostgreSQL table.

Validates CSV columns against a required-fields JSON file and the target
table schema, then inserts rows in batches using ``ON CONFLICT DO NOTHING``
to safely skip duplicates.
"""

import argparse
import csv
import json
import logging
import os
import psycopg2
from psycopg2 import sql
import sys


def table_exists(conn, table):
    """Check whether a table exists in the current database.

    Args:
        conn: Active psycopg2 connection.
        table: Name of the table to look up.

    Returns:
        True if the table exists, False otherwise.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            (table,)
        )
        return cur.fetchone()[0]


def get_table_columns(conn, table):
    """Return the list of column names for a given table.

    Args:
        conn: Active psycopg2 connection.
        table: Name of the table.

    Returns:
        List of column name strings.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
            (table,)
        )
        return [r[0] for r in cur.fetchall()]


def get_primary_key_columns(conn, table):
    """Return the list of primary key column names for a given table.

    Args:
        conn: Active psycopg2 connection.
        table: Name of the table.

    Returns:
        List of column name strings in primary key order, or empty list if no PK.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s AND constraint_name = (
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_name = %s AND constraint_type = 'PRIMARY KEY'
            )
            ORDER BY ordinal_position
            """,
            (table, table)
        )
        return [r[0] for r in cur.fetchall()]




def load_required_map(path):
    """Load the required-fields JSON file.

    The file must be a JSON object mapping table names to lists of
    required column names, e.g. ``{"runs": ["run_id", "day_id"]}``.

    Args:
        path: File-system path to the JSON file.

    Returns:
        dict mapping table name → list of required column names.

    Raises:
        ValueError: If the file does not contain a JSON object.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("required columns file must be a JSON object {table: [cols...]}")
    return data


def normalize_long_format_row(row):
    """Ensure ``value_number`` is ``None`` when empty.

    The sequencing_qc_metrics table uses a long format where each row
    has a single numeric value. Empty strings from the CSV must be
    converted to ``None`` so PostgreSQL stores a proper NULL.

    Args:
        row: Dict representing one CSV row (modified in place).

    Returns:
        The same dict, with ``value_number`` normalised.
    """
    if row.get("value_number") in {"", None}:
        row["value_number"] = None
    return row


def main():
    """CLI entry point: parse arguments, validate inputs, and load a CSV into PostgreSQL.

    Workflow:
      1. Parse CLI arguments (host, port, db, user, password, table, csv, fields).
      2. Validate that the CSV and required-fields JSON exist.
      3. Connect to the database and verify the target table exists.
      4. Cross-check CSV columns against required columns and table schema.
      5. Detect existing primary-key rows to avoid duplicates.
      6. Insert rows in batches using ``ON CONFLICT DO NOTHING``.

    Returns:
        0 on success, 2 on validation/connection errors.
    """
    ap = argparse.ArgumentParser(description="Load CSV into PostgreSQL table.")
    ap.add_argument("--host", default="db", help="Postgres host")
    ap.add_argument("--port", default="5432", help="Postgres port")
    ap.add_argument("--db", required=True, help="Postgres database name")
    ap.add_argument("--user", default="postgres", help="Postgres user")
    ap.add_argument("--password", default="postgres", help="Postgres password")
    ap.add_argument("--table", required=True, help="Target table name")
    ap.add_argument("--csv", required=True, help="CSV file path")
    ap.add_argument("--fields", required=True, help="JSON file mapping table, required fields list")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Fail if CSV includes columns not present in the table (default: ignore extra CSV columns).",
    )
    ap.add_argument("--batch-size", type=int, default=1000, help="Batch size for inserts (default: 1000)")
    ap.add_argument("--log", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = ap.parse_args()

    logging.basicConfig(level=args.log.upper(), format='%(levelname)s:%(message)s')

    csv_path = os.path.abspath(args.csv)
    fields_path = os.path.abspath(args.fields)

    logging.info(f"CSV path: {csv_path}")
    logging.info(f"Fields path: {fields_path}")

    if not os.path.exists(csv_path):
        logging.error("CSV not found: %s", csv_path)
        return 2
    if not os.path.exists(fields_path):
        logging.error("Required fields file not found: %s", fields_path)
        return 2

    required_map = load_required_map(fields_path)
    required_cols = required_map.get(args.table)
    logging.info(f"Required columns for table '{args.table}': {required_cols}")
    if required_cols is None:
        logging.error("No required columns defined for table %r in %s", args.table, fields_path)
        return 2

    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.db,
        user=args.user,
        password=args.password
    )
    logging.info("Connected to database: %s", args.db)
    try:
        if not table_exists(conn, args.table):
            logging.error("Table does not exist: %s", args.table)
            return 2

        table_cols = get_table_columns(conn, args.table)
        table_set = set(table_cols)
        logging.info(f"Table columns: {table_cols}")

        # Ensure required columns exist in the table
        missing_in_table = [c for c in required_cols if c not in table_set]
        if missing_in_table:
            logging.error(
                "Required columns %s declared for table %s but not present in the table schema",
                missing_in_table,
                args.table,
            )
            return 2

        # Read CSV headers quickly to decide which columns to insert
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
        logging.info(f"CSV columns: {headers}")

        # Check required columns exist in CSV
        missing_required = [c for c in required_cols if c not in headers]
        if missing_required:
            # Special case: skip sample_qc_metrics if library_id is missing (run hasn't been enriched)
            if args.table == "sample_qc_metrics" and missing_required == ["library_id"]:
                logging.info("Skipping sample_qc_metrics: not enriched with library_id")
                return 0
            logging.error("CSV missing required columns for %s: %s", args.table, missing_required)
            return 2

        # Identify extra CSV columns
        extra = [h for h in headers if h not in table_set]
        if extra and args.strict:
            logging.error("CSV contains columns not in table %s: %s", args.table, extra)
            return 2

        # Only insert columns present in table
        insert_cols = [h for h in headers if h in table_set]
        if not insert_cols:
            logging.error("No CSV columns match table columns")
            return 2

        # Get primary key columns to use in ON CONFLICT
        pk_cols = get_primary_key_columns(conn, args.table)
        if not pk_cols:
            logging.warning(f"Table {args.table} has no primary key; using ON CONFLICT DO NOTHING without column specification")
            pk_cols_sql = None
        else:
            logging.info(f"Primary key columns for {args.table}: {pk_cols}")
            pk_cols_sql = sql.SQL(', ').join(map(sql.Identifier, pk_cols))

        cols_sql = sql.SQL(', ').join(map(sql.Identifier, insert_cols))
        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(insert_cols))
        table_sql = sql.Identifier(args.table)
        
        if pk_cols_sql:
            insert_sql = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values}) ON CONFLICT ({pk_cols}) DO NOTHING").format(
                table=table_sql,
                fields=cols_sql,
                values=placeholders,
                pk_cols=pk_cols_sql
            )
        else:
            insert_sql = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values}) ON CONFLICT DO NOTHING").format(
                table=table_sql,
                fields=cols_sql,
                values=placeholders
            )

        # Insert rows in batches
        inserted = 0
        skipped = 0
        invalid_fk = 0
        batch_size = args.batch_size
        batch = []
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                # Transform undetermined sample IDs to undetermined_<run_id>
                if args.table == "sample_qc_metrics":
                    sample_id = row.get("sample_id", "").strip().lower()
                    if "undetermined" in sample_id or sample_id.startswith("ud"):
                        run_id = row.get("run_id", "unknown").strip()
                        row["sample_id"] = f"undetermined_{run_id}"
                        logging.debug(f"Row {idx}: Transformed sample_id to {row['sample_id']}")
                
                values = [row[col] if row[col] != "" else None for col in insert_cols]
                logging.debug(f"Row {idx}: {values}")
                batch.append(values)
                if len(batch) >= batch_size:
                    try:
                        with conn.cursor() as cur:
                            cur.executemany(insert_sql.as_string(conn), batch)
                            rows_affected = cur.rowcount
                        conn.commit()
                        inserted += rows_affected
                        skipped += len(batch) - rows_affected
                        batch.clear()
                    except Exception as e:
                        logging.error(f"Failed to insert batch ending at row {idx}: {e}")
                        conn.rollback()
            if batch:
                try:
                    with conn.cursor() as cur:
                        cur.executemany(insert_sql.as_string(conn), batch)
                        rows_affected = cur.rowcount
                    conn.commit()
                    inserted += rows_affected
                    skipped += len(batch) - rows_affected
                except Exception as e:
                    logging.error(f"Failed to insert final batch: {e}")
                    conn.rollback()

        logging.info("Loaded %d rows into '%s' from %s", inserted, args.table, os.path.basename(csv_path))
        if skipped > 0:
            logging.info("Skipped %d duplicate rows (already in database)", skipped)
        logging.info("Inserted columns: %s", insert_cols)
        if extra and not args.strict:
            logging.warning("Ignored extra CSV columns (not in table): %s", extra)

        return 0

    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())
