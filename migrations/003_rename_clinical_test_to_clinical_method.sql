-- Rename the sample clinical classification without changing existing values.
BEGIN;
ALTER TABLE samples RENAME COLUMN clinical_test TO clinical_method;
COMMIT;
