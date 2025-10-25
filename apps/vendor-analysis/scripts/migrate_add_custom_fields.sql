-- Migration: Add JSONB columns for custom fields and raw data
-- Purpose: Enable schema-resilient storage of NetSuite custom fields
-- Date: 2025-01-24
--
-- This migration adds:
-- 1. custom_fields JSONB column - stores NetSuite custom fields with lifecycle metadata
-- 2. raw_data JSONB column - stores complete NetSuite API response for auditing
-- 3. schema_version INTEGER column - tracks which fields were available at sync time
--
-- Safe to run multiple times (uses IF NOT EXISTS)

BEGIN;

-- ============================================================================
-- VENDORS TABLE
-- ============================================================================

-- Add custom_fields column to vendors table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'custom_fields'
    ) THEN
        ALTER TABLE vendors
        ADD COLUMN custom_fields JSONB;

        COMMENT ON COLUMN vendors.custom_fields IS
            'Custom NetSuite fields (custentity_*) with lifecycle metadata';
    END IF;
END $$;

-- Add raw_data column to vendors table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'raw_data'
    ) THEN
        ALTER TABLE vendors
        ADD COLUMN raw_data JSONB;

        COMMENT ON COLUMN vendors.raw_data IS
            'Complete NetSuite API response for auditing';
    END IF;
END $$;

-- Add schema_version column to vendors table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'schema_version'
    ) THEN
        ALTER TABLE vendors
        ADD COLUMN schema_version INTEGER;

        COMMENT ON COLUMN vendors.schema_version IS
            'Tracks which fields were available at sync time (timestamp-based)';
    END IF;
END $$;

-- Create GIN index on custom_fields for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_vendors_custom_fields_gin
ON vendors USING GIN (custom_fields);

-- Create index on schema_version for analysis queries
CREATE INDEX IF NOT EXISTS idx_vendors_schema_version
ON vendors (schema_version);

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================

-- Add custom_fields column to transactions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'custom_fields'
    ) THEN
        ALTER TABLE transactions
        ADD COLUMN custom_fields JSONB;

        COMMENT ON COLUMN transactions.custom_fields IS
            'Custom NetSuite transaction fields (custbody_*) with lifecycle metadata';
    END IF;
END $$;

-- Add raw_data column to transactions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'raw_data'
    ) THEN
        ALTER TABLE transactions
        ADD COLUMN raw_data JSONB;

        COMMENT ON COLUMN transactions.raw_data IS
            'Complete NetSuite API response for auditing';
    END IF;
END $$;

-- Add schema_version column to transactions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'schema_version'
    ) THEN
        ALTER TABLE transactions
        ADD COLUMN schema_version INTEGER;

        COMMENT ON COLUMN transactions.schema_version IS
            'Tracks which fields were available at sync time (timestamp-based)';
    END IF;
END $$;

-- Create GIN index on custom_fields for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_transactions_custom_fields_gin
ON transactions USING GIN (custom_fields);

-- Create index on schema_version for analysis queries
CREATE INDEX IF NOT EXISTS idx_transactions_schema_version
ON transactions (schema_version);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to extract simple values from custom_fields metadata structure
CREATE OR REPLACE FUNCTION get_custom_field_value(
    custom_fields_json JSONB,
    field_name TEXT
) RETURNS TEXT AS $$
DECLARE
    field_data JSONB;
BEGIN
    field_data := custom_fields_json -> field_name;

    IF field_data IS NULL THEN
        RETURN NULL;
    END IF;

    -- If it has metadata structure, extract value
    IF field_data ? 'value' THEN
        RETURN field_data ->> 'value';
    ELSE
        -- Old format - return as-is
        RETURN field_data::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION get_custom_field_value IS
    'Extract custom field value from metadata structure for queries';

-- Function to check if custom field is deprecated
CREATE OR REPLACE FUNCTION is_custom_field_deprecated(
    custom_fields_json JSONB,
    field_name TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    field_data JSONB;
BEGIN
    field_data := custom_fields_json -> field_name;

    IF field_data IS NULL THEN
        RETURN TRUE;  -- Field doesn't exist = considered deprecated
    END IF;

    IF field_data ? 'deprecated' THEN
        RETURN (field_data ->> 'deprecated')::BOOLEAN;
    ELSE
        RETURN FALSE;  -- Old format - assume not deprecated
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION is_custom_field_deprecated IS
    'Check if custom field is marked as deprecated (not seen in recent syncs)';

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Verify columns were added
DO $$
DECLARE
    vendor_custom_fields_exists BOOLEAN;
    vendor_raw_data_exists BOOLEAN;
    vendor_schema_version_exists BOOLEAN;
    transaction_custom_fields_exists BOOLEAN;
    transaction_raw_data_exists BOOLEAN;
    transaction_schema_version_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'custom_fields'
    ) INTO vendor_custom_fields_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'raw_data'
    ) INTO vendor_raw_data_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'vendors' AND column_name = 'schema_version'
    ) INTO vendor_schema_version_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'custom_fields'
    ) INTO transaction_custom_fields_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'raw_data'
    ) INTO transaction_raw_data_exists;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions' AND column_name = 'schema_version'
    ) INTO transaction_schema_version_exists;

    IF vendor_custom_fields_exists AND vendor_raw_data_exists AND vendor_schema_version_exists
       AND transaction_custom_fields_exists AND transaction_raw_data_exists AND transaction_schema_version_exists THEN
        RAISE NOTICE 'Migration completed successfully!';
        RAISE NOTICE '  ✓ vendors.custom_fields added';
        RAISE NOTICE '  ✓ vendors.raw_data added';
        RAISE NOTICE '  ✓ vendors.schema_version added';
        RAISE NOTICE '  ✓ transactions.custom_fields added';
        RAISE NOTICE '  ✓ transactions.raw_data added';
        RAISE NOTICE '  ✓ transactions.schema_version added';
        RAISE NOTICE '  ✓ GIN indexes created';
        RAISE NOTICE '  ✓ Helper functions created';
    ELSE
        RAISE EXCEPTION 'Migration failed - not all columns were created';
    END IF;
END $$;
