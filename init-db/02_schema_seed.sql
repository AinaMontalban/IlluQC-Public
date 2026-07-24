-- IlluQC Database Schema – Seed / Reference Data
-- Adapted for Multi-Platform Sequencing QC
--
-- This file is executed AFTER 01_schema_ddl.sql (alphabetical order).
-- To add a new metric, append an INSERT to the appropriate section below.
-- The Streamlit app reads display_label automatically — no code changes needed.

-- =========================
-- Sequencing Platforms
-- =========================

INSERT INTO sequencing_platforms(platform_id, platform_name) VALUES
('ILLUMINA', 'Illumina'),
('THERMOFISHER', 'Thermo Fisher (Ion Torrent)')
ON CONFLICT (platform_id) DO NOTHING;

-- =========================
-- Chemistry Attribute Definitions
-- =========================

-- Illumina
INSERT INTO chemistry_attribute_definitions(attribute_id, attribute_name, platform_id, description) VALUES
('FLOWCELL_NAME',           'Flowcell name',            'ILLUMINA',     'Illumina flowcell / dry-cartridge name'),
('FLOWCELL_PART_NUMBER',    'Flowcell part number',     'ILLUMINA',     'Illumina flowcell part number'),
('REAGENT_KIT_NAME',        'Reagent kit name',         'ILLUMINA',     'Illumina reagent / wet-cartridge name'),
('REAGENT_KIT_PART_NUMBER', 'Reagent kit part number',  'ILLUMINA',     'Illumina reagent kit part number')
ON CONFLICT (attribute_id) DO NOTHING;

-- Thermo Fisher / Ion Torrent
INSERT INTO chemistry_attribute_definitions(attribute_id, attribute_name, platform_id, description) VALUES
('CHIP_TYPE',               'Chip type',                'THERMOFISHER', 'Ion Torrent chip type (e.g. 530, 520)'),
('CHIP_BARCODE',            'Chip barcode',             'THERMOFISHER', 'Ion Torrent chip barcode'),
('CHEF_REAGENTS_PART',      'Chef reagents part',       'THERMOFISHER', 'Ion Chef reagents part number'),
('TEMPLATING_KIT_NAME',     'Templating kit name',      'THERMOFISHER', 'Ion Chef templating kit'),
('LIBRARY_KIT_NAME',        'Library kit name',         'THERMOFISHER', 'Library preparation kit'),
('SEQUENCING_KIT_NAME',     'Sequencing kit name',      'THERMOFISHER', 'Ion Torrent sequencing kit')
ON CONFLICT (attribute_id) DO NOTHING;

-- =========================
-- Day Dimension (pre-populated date range)
-- =========================

INSERT INTO day (day_id)
SELECT d::date
FROM generate_series('2020-01-01'::date, '2050-12-31'::date, interval '1 day') AS t(d)
ON CONFLICT DO NOTHING;

-- =========================
-- QC Metric Definitions
-- =========================
-- To add a new metric, just append an INSERT here.
-- The app picks up display_label automatically from the database.

-- Illumina run-level metrics

-- Example Illumina metric definitions (maps to your current columns)
INSERT INTO qc_metric_definitions(metric_id, metric_name, display_label, platform_id, unit, value_type, description) VALUES
('CLUSTER_DENSITY_MEAN',        'cluster_density_mean',    'Cluster Density (K/mm²)',  'ILLUMINA', 'k/mm2', 'number', 'Cluster density'),
('CLUSTER_PF_PCT_MEAN',         'cluster_pf_mean',         '% PF Clusters',           'ILLUMINA', '%',     'number', 'Percent clusters passing filter'),
('Q30_PCT_MEAN',                'q30_mean',                '% Q30 Reads',             'ILLUMINA', '%',     'number', 'Percent bases with Q>=30'),
('YIELD_MEAN',                  'yield_mean',              'Yield (Gb)',              'ILLUMINA', 'GB',    'number', 'Total yield'),
('PHIX_ALIGNED_PCT_MEAN',       'percent_phix_aligned_mean','% PhiX Aligned',         'ILLUMINA', '%',     'number', 'Percent PhiX aligned'),
('ERROR_RATE_MEAN',             'error_rate_mean',         'Error Rate (%)',          'ILLUMINA', '%',     'number', 'Mean error rate'),
('PCT_OCCUPIED_MEAN',           'pct_occupied_mean',       '% Occupied',              'ILLUMINA', '%',     'number', 'Percent occupied wells'),
('READS_MEAN',                  'reads_mean',              'Total Reads',             'ILLUMINA', 'reads', 'number', 'Mean total reads'),
('READS_PF_MEAN',               'reads_pf_mean',           'Reads PF',                'ILLUMINA', 'reads', 'number', 'Mean reads passing filter'),
('YIELD_READ_1',                'yield_read_1',            'Yield Read 1 (Gb)',       'ILLUMINA', 'GB',    'number', 'Yield for read 1'),
('Q30_PCT_READ_1',              'q30_pct_read_1',          '% Q30 Read 1',            'ILLUMINA', '%',     'number', 'Percent Q30 bases in read 1'),
('ERROR_RATE_READ_1',           'error_rate_read_1',       'Error Rate Read 1 (%)',   'ILLUMINA', '%',     'number', 'Error rate for read 1'),
('YIELD_READ_2',                'yield_read_2',            'Yield Read 2 (Gb)',       'ILLUMINA', 'GB',    'number', 'Yield for read 2'),
('Q30_PCT_READ_2',              'q30_pct_read_2',          '% Q30 Read 2',            'ILLUMINA', '%',     'number', 'Percent Q30 bases in read 2'),
('ERROR_RATE_READ_2',           'error_rate_read_2',       'Error Rate Read 2 (%)',   'ILLUMINA', '%',     'number', 'Error rate for read 2'),
('YIELD_READ_3',                'yield_read_3',            'Yield Read 3 (Gb)',       'ILLUMINA', 'GB',    'number', 'Yield for read 3'),
('Q30_PCT_READ_3',              'q30_pct_read_3',          '% Q30 Read 3',            'ILLUMINA', '%',     'number', 'Percent Q30 bases in read 3'),
('ERROR_RATE_READ_3',           'error_rate_read_3',       'Error Rate Read 3 (%)',   'ILLUMINA', '%',     'number', 'Error rate for read 3'),
('YIELD_READ_4',                'yield_read_4',            'Yield Read 4 (Gb)',       'ILLUMINA', 'GB',    'number', 'Yield for read 4'),
('Q30_PCT_READ_4',              'q30_pct_read_4',          '% Q30 Read 4',            'ILLUMINA', '%',     'number', 'Percent Q30 bases in read 4'),
('ERROR_RATE_READ_4',           'error_rate_read_4',       'Error Rate Read 4 (%)',   'ILLUMINA', '%',     'number', 'Error rate for read 4')
ON CONFLICT (metric_id) DO NOTHING;


-- Thermo Fisher / Ion Torrent run-level metrics
INSERT INTO qc_metric_definitions(metric_id, metric_name, display_label, workflow_step, platform_id, unit, value_type, description) VALUES
('READS_TOTAL',        'total_reads',        'Total Reads',            'sequencing', 'THERMOFISHER', 'reads', 'number', 'Total reads produced'),
('READ_LENGTH_MEAN',   'mean_read_length',   'Mean Read Length (bp)',   'sequencing', 'THERMOFISHER', 'bp',    'number', 'Average read length'),
('Q20_BASES_PCT',      'q20_bases_pct',      '% Bases ≥ Q20',         'sequencing', 'THERMOFISHER', '%',     'number', 'Percent bases with Q>=20'),
('LOADING_PCT',        'loading_pct',        'Loading %',              'sequencing', 'THERMOFISHER', '%',     'number', 'Chip loading percentage'),
('ADDRESS_AVAILABLE',  'address_available',  'Address Available',      'sequencing', 'THERMOFISHER', 'Wells', 'number', 'Well Addresses available')
ON CONFLICT (metric_id) DO NOTHING;

-- FastQC per-sample metrics (scope = sample, platform-agnostic)
-- Read-specific variants for R1 and R2
INSERT INTO qc_metric_definitions(metric_id, metric_name, display_label, workflow_step, scope, unit, value_type, description) VALUES
('FASTQC_TOTAL_SEQUENCES_R1',       'Total sequences R1',       'Total Sequences R1',             'demultiplexing', 'sample', 'reads',  'number', 'Total number of sequences in FASTQ R1'),
('FASTQC_TOTAL_SEQUENCES_R2',       'Total sequences R2',       'Total Sequences R2',             'demultiplexing', 'sample', 'reads',  'number', 'Total number of sequences in FASTQ R2'),
('FASTQC_PERCENT_FAILS_R1',         'Percent fails R1',         'Percent Fails R1 (%)',           'demultiplexing', 'sample', '%',      'number', 'Percentage of sequences failing QC checks R1'),
('FASTQC_PERCENT_FAILS_R2',         'Percent fails R2',         'Percent Fails R2 (%)',           'demultiplexing', 'sample', '%',      'number', 'Percentage of sequences failing QC checks R2'),
('FASTQC_GC_PCT_R1',                'Percent GC R1',            'GC Content R1 (%)',              'demultiplexing', 'sample', '%',      'number', 'GC content percentage R1'),
('FASTQC_GC_PCT_R2',                'Percent GC R2',            'GC Content R2 (%)',              'demultiplexing', 'sample', '%',      'number', 'GC content percentage R2'),
('FASTQC_PERCENT_DUPLICATES_R1',    'Percent duplicates R1',    'Duplicates R1 (%)',              'demultiplexing', 'sample', '%',      'number', 'Percentage of duplicate reads R1'),
('FASTQC_PERCENT_DUPLICATES_R2',    'Percent duplicates R2',    'Duplicates R2 (%)',              'demultiplexing', 'sample', '%',      'number', 'Percentage of duplicate reads R2'),
('FASTQC_AVG_SEQUENCE_LENGTH_R1',   'Avg sequence length R1',   'Avg Sequence Length R1 (bp)',    'demultiplexing', 'sample', 'bp',     'number', 'Average sequence length R1'),
('FASTQC_AVG_SEQUENCE_LENGTH_R2',   'Avg sequence length R2',   'Avg Sequence Length R2 (bp)',    'demultiplexing', 'sample', 'bp',     'number', 'Average sequence length R2'),
('total_reads', 'total reads', 'total reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Total number of sequencing reads'),
('primary_reads', 'primary reads', 'primary reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of primary reads'),
('prop_primary_reads', 'prop primary reads', 'prop primary reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of primary reads'),
('secondary_reads', 'secondary reads', 'secondary reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of secondary reads'),
('prop_secondary_reads', 'prop secondary reads', 'prop secondary reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of secondary reads'),
('supplementary_reads', 'supplementary reads', 'supplementary reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of supplementary reads'),
('prop_supplementary_reads', 'prop supplementary reads', 'prop supplementary reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of supplementary reads'),
('duplicate_reads', 'duplicate reads', 'duplicate reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of duplicate reads'),
('prop_duplicate_reads', 'prop duplicate reads', 'prop duplicate reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of duplicate reads'),
('mapped_reads', 'mapped reads', 'mapped reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of mapped reads'),
('prop_mapped_reads', 'prop mapped reads', 'prop mapped reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of mapped reads'),
('mapped_good_reads', 'mapped good reads', 'mapped good reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of high-quality mapped reads'),
('prop_mapped_good_reads_of_mapped_reads', 'prop mapped good reads of mapped reads', 'prop mapped good reads of mapped reads', 'QC', 'sample', '%', 'FLOAT', 'Proportion of high-quality mapped reads among mapped reads'),
('prop_mapped_good_reads_of_total_reads', 'prop mapped good reads of total reads', 'prop mapped good reads of total reads', 'QC', 'sample', '%', 'FLOAT', 'Proportion of high-quality mapped reads among total reads'),
('ontarget_reads', 'ontarget reads', 'ontarget reads', 'BAM QC', 'sample', 'reads', 'INTEGER', 'Number of reads mapping to target regions'),
('prop_ontarget_reads_of_mapped_good_reads', 'prop ontarget reads of mapped good reads', 'prop ontarget reads of mapped good reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of on-target reads among high-quality mapped reads'),
('prop_ontarget_reads_of_total_reads', 'prop ontarget reads of total reads', 'prop ontarget reads of total reads', 'BAM QC', 'sample', '%', 'FLOAT', 'Proportion of on-target reads among total reads'),
('Cov_1X', 'Cov 1X', 'Cov 1X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 1X'),
('Cov_20X', 'Cov 20X', 'Cov 20X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 20X'),
('Cov_38X', 'Cov 38X', 'Cov 38X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 38X'),
('Cov_75X', 'Cov 75X', 'Cov 75X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 75X'),
('Cov_100X', 'Cov 100X', 'Cov 100X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 100X'),
('Cov_250X', 'Cov 250X', 'Cov 250X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 250X'),
('Cov_500X', 'Cov 500X', 'Cov 500X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 500X'),
('Cov_1000X', 'Cov 1000X', 'Cov 1000X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 1000X'),
('Cov_2000X', 'Cov 2000X', 'Cov 2000X', 'BAM QC', 'sample', '%', 'FLOAT', 'Percentage of target bases covered at least 2000X'),
('mean', 'mean', 'mean', 'BAM QC', 'sample', 'X', 'FLOAT', 'Mean sequencing coverage'),
('min', 'min', 'min', 'BAM QC', 'sample', 'X', 'INTEGER', 'Minimum sequencing coverage'),
('max', 'max', 'max', 'BAM QC', 'sample', 'X', 'INTEGER', 'Maximum sequencing coverage'),
('Coverage_Uniformity', 'Coverage Uniformity', 'Coverage Uniformity', 'BAM QC', 'sample', '%', 'FLOAT', 'Coverage uniformity across target regions');
ON CONFLICT (metric_id) DO NOTHING;

-- =========================
-- Schema Metadata
-- =========================

INSERT INTO schema_metadata (key, value) VALUES
('schema_name', 'IlluQC Database'),
('schema_version', '1.0')
ON CONFLICT (key) DO NOTHING;
