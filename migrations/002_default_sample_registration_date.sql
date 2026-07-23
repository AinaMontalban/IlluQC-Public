-- Assign the database insertion date to new sample rows.
-- Existing rows, including rows with NULL registration_date, are unchanged.
BEGIN;
ALTER TABLE samples
  ALTER COLUMN registration_date SET DEFAULT CURRENT_DATE;
COMMIT;
