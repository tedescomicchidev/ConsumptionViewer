-- MACC Consumption Viewer Database Schema
-- Schema Version: v1
-- Last Updated: 2026-02-16

-- Table: datasets
CREATE TABLE datasets (
    dataset_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    name NVARCHAR(200) NULL,
    original_filename NVARCHAR(400) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    created_by NVARCHAR(200) NOT NULL,
    current_revision_id UNIQUEIDENTIFIER NULL,
    schema_version NVARCHAR(50) NOT NULL DEFAULT 'v1',
    CONSTRAINT PK_datasets PRIMARY KEY (dataset_id)
);

-- Table: dataset_revisions
CREATE TABLE dataset_revisions (
    revision_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    dataset_id UNIQUEIDENTIFIER NOT NULL,
    revision_number INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    created_by NVARCHAR(200) NOT NULL,
    change_summary NVARCHAR(MAX) NULL,
    CONSTRAINT PK_dataset_revisions PRIMARY KEY (revision_id),
    CONSTRAINT FK_dataset_revisions_datasets FOREIGN KEY (dataset_id)
        REFERENCES datasets(dataset_id) ON DELETE CASCADE
);

-- Table: plan_rows
CREATE TABLE plan_rows (
    row_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    revision_id UNIQUEIDENTIFIER NOT NULL,
    workload NVARCHAR(300) NOT NULL,
    scenario NVARCHAR(100) NOT NULL,
    azure_services NVARCHAR(800) NOT NULL,
    start_month NVARCHAR(30) NOT NULL,
    ramp_up_duration_months INT NOT NULL,
    ramp_up_start_consumption DECIMAL(18,2) NOT NULL,
    steady_state_monthly_consumption DECIMAL(18,2) NOT NULL,
    avg_monthly_ramp_up_consumption DECIMAL(18,2) NOT NULL,
    total_ramp_up_consumption DECIMAL(18,2) NOT NULL,
    year1_steady_state_months INT NOT NULL,
    year1_steady_state_consumption DECIMAL(18,2) NOT NULL,
    total_year1_estimated_acr DECIMAL(18,2) NOT NULL,
    extras_json NVARCHAR(MAX) NULL,
    CONSTRAINT PK_plan_rows PRIMARY KEY (row_id),
    CONSTRAINT FK_plan_rows_revisions FOREIGN KEY (revision_id)
        REFERENCES dataset_revisions(revision_id) ON DELETE CASCADE,
    CONSTRAINT CHK_ramp_up_duration CHECK (ramp_up_duration_months >= 0 AND ramp_up_duration_months <= 12),
    CONSTRAINT CHK_year1_steady_months CHECK (year1_steady_state_months >= 0 AND year1_steady_state_months <= 12)
);

-- Table: audit_log
CREATE TABLE audit_log (
    audit_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    dataset_id UNIQUEIDENTIFIER NULL,
    revision_id UNIQUEIDENTIFIER NULL,
    actor NVARCHAR(200) NOT NULL,
    action NVARCHAR(50) NOT NULL,
    timestamp DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    details_json NVARCHAR(MAX) NULL,
    CONSTRAINT PK_audit_log PRIMARY KEY (audit_id)
);

-- Indexes for performance
CREATE INDEX IX_dataset_revisions_dataset_id ON dataset_revisions(dataset_id);
CREATE INDEX IX_plan_rows_revision_id ON plan_rows(revision_id);
CREATE INDEX IX_audit_log_dataset_id ON audit_log(dataset_id);
CREATE INDEX IX_audit_log_timestamp ON audit_log(timestamp);
