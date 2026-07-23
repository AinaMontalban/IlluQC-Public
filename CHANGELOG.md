# Changelog

## Unreleased

- Renamed the project-facing CLI and dashboard terminology to IlluQC.
- Standardized operational commands under the `illuqc` launcher.
- Required Docker Compose v2 and removed the legacy Compose fallback.
- Organized scripts into runtime, run, sample, lab, database, shared-library, legacy,
  and tool directories.
- Added validated run-wide and single-sample preparation/loading workflows.
- Added database-generated sample registration dates and renamed
  `clinical_test` to `clinical_method`.
- Removed discontinued chemistry-attribute tables and documented migrations.
- Added the About dashboard page with application and schema versions.
- Rebuilt the synthetic demo around 11 MiSeq runs, HLA/ALLOSEQ libraries,
  MiSeq v2/v3 chemistries, and repeated samples across matching chemistry.
- Improved demo terminal reporting, password handling, documentation, and
  operational safety guidance.
