-- Migration: Add incremental sync support
-- Description: Adds timestamp tracking and soft delete columns for incremental sync
-- Date: 2025-01-24

BEGIN;

-- Add timestamp columns to vendors table
ALTER TABLE vendors
    ADD COLUMN IF NOT EXISTS created_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN vendors.created_date IS 'NetSuite dateCreated timestamp';
COMMENT ON COLUMN vendors.is_deleted IS 'Soft delete flag (not in NetSuite)';

-- Add timestamp columns to transactions table
ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS created_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_modified_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN transactions.created_date IS 'NetSuite createdDate timestamp';
COMMENT ON COLUMN transactions.last_modified_date IS 'NetSuite lastModifiedDate timestamp';
COMMENT ON COLUMN transactions.is_deleted IS 'Soft delete flag (not in NetSuite)';

-- Create sync_metadata table
CREATE TABLE IF NOT EXISTS sync_metadata (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(50) NOT NULL UNIQUE,
    last_sync_timestamp TIMESTAMP NOT NULL,
    sync_status VARCHAR(20) NOT NULL DEFAULT 'completed',
    records_synced INTEGER NOT NULL DEFAULT 0,
    is_full_sync BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_metadata_record_type ON sync_metadata(record_type);

COMMENT ON TABLE sync_metadata IS 'Tracks sync operations for incremental updates';
COMMENT ON COLUMN sync_metadata.record_type IS 'vendor or vendorbill';
COMMENT ON COLUMN sync_metadata.last_sync_timestamp IS 'Last successful sync completion time';
COMMENT ON COLUMN sync_metadata.sync_status IS 'completed, in_progress, failed';
COMMENT ON COLUMN sync_metadata.records_synced IS 'Number of records synced in last operation';
COMMENT ON COLUMN sync_metadata.is_full_sync IS 'Was this a full sync or incremental';

COMMIT;
