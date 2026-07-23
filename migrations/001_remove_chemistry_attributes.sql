-- Remove discontinued chemistry-attribute tables from an existing database.
BEGIN;
DROP TABLE IF EXISTS sequencing_chemistry_attributes;
DROP TABLE IF EXISTS chemistry_attribute_definitions;
COMMIT;
