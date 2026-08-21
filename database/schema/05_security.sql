-- ============================================================================
-- DATABASE SECURITY
-- Roles, privileges and Row Level Security for the SOC data platform.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. AUTHORIZATION ROLES
-- NOLOGIN roles represent capabilities only.
-- Runtime identities must be associated with these roles outside this repository.
-- ----------------------------------------------------------------------------
BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'soc_pipeline'
    ) THEN
        CREATE ROLE soc_pipeline NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'threat_intel_writer'
    ) THEN
        CREATE ROLE threat_intel_writer NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'soc_auditor'
    ) THEN
        CREATE ROLE soc_auditor NOLOGIN;
    END IF;
END
$$;


-- ----------------------------------------------------------------------------
-- 2. ROW LEVEL SECURITY
-- Raw operational tables remain protected even if privileges are accidentally
-- granted to another role in the future.
-- ----------------------------------------------------------------------------

ALTER TABLE tbl_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_contas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_logs_seguranca ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_auditoria_acessos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_mitre_mapping ENABLE ROW LEVEL SECURITY;


-- ----------------------------------------------------------------------------
-- 3. REMOVE BROAD ACCESS
-- Explicitly remove privileges inherited through PUBLIC and default Supabase
-- API roles. Application access is granted only to dedicated capabilities.
-- ----------------------------------------------------------------------------

REVOKE ALL ON TABLE tbl_clientes
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE tbl_contas
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE tbl_transacoes
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE tbl_logs_seguranca
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE tbl_auditoria_acessos
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE tbl_mitre_mapping
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE v_analise_investigacao_soc
    FROM PUBLIC, anon, authenticated;

REVOKE ALL
    ON SEQUENCE tbl_auditoria_acessos_id_auditoria_seq
    FROM PUBLIC, anon, authenticated;


-- ----------------------------------------------------------------------------
-- 4. SOC PIPELINE
-- The detector consumes only the minimized investigation view, reads threat
-- intelligence and records its own access audit event.
-- ----------------------------------------------------------------------------

GRANT SELECT
    ON v_analise_investigacao_soc
    TO soc_pipeline;

GRANT SELECT
    ON tbl_mitre_mapping
    TO soc_pipeline;

GRANT INSERT
    ON tbl_auditoria_acessos
    TO soc_pipeline;

GRANT USAGE
    ON SEQUENCE tbl_auditoria_acessos_id_auditoria_seq
    TO soc_pipeline;

GRANT USAGE
    ON SCHEMA public
    TO soc_pipeline, threat_intel_writer, soc_auditor;


-- ----------------------------------------------------------------------------
-- 5. THREAT INTELLIGENCE WRITER
-- Dedicated capability used only by the MITRE ATT&CK ingestion process.
-- ----------------------------------------------------------------------------

GRANT INSERT, TRUNCATE
    ON tbl_mitre_mapping
    TO threat_intel_writer;


-- ----------------------------------------------------------------------------
-- 6. AUDITOR
-- Read-only access to accountability records.
-- ----------------------------------------------------------------------------

GRANT SELECT
    ON tbl_auditoria_acessos
    TO soc_auditor;


-- ----------------------------------------------------------------------------
-- 7. LEGACY POLICY CLEANUP
-- Remove policies created by previous iterations of the database security model.
-- These statements are intentionally safe to reapply.
-- ----------------------------------------------------------------------------

DROP POLICY IF EXISTS admin_full_access_clientes
    ON tbl_clientes;

DROP POLICY IF EXISTS admin_full_access_contas
    ON tbl_contas;

DROP POLICY IF EXISTS admin_full_access_transacoes
    ON tbl_transacoes;

DROP POLICY IF EXISTS admin_full_access_logs
    ON tbl_logs_seguranca;

DROP POLICY IF EXISTS admin_full_access_auditoria
    ON tbl_auditoria_acessos;

DROP POLICY IF EXISTS "Allow public read"
    ON tbl_mitre_mapping;

DROP POLICY IF EXISTS "Authenticated users can read MITRE mappings"
    ON tbl_mitre_mapping;

-- ----------------------------------------------------------------------------
-- 8. RLS POLICIES
-- Policies are recreated explicitly so this security script can be reapplied
-- safely and remains the canonical definition of the authorization model.
-- ----------------------------------------------------------------------------

DROP POLICY IF EXISTS soc_pipeline_insert_audit
    ON tbl_auditoria_acessos;

CREATE POLICY soc_pipeline_insert_audit
    ON tbl_auditoria_acessos
    FOR INSERT
    TO soc_pipeline
    WITH CHECK (true);


DROP POLICY IF EXISTS soc_auditor_read_audit
    ON tbl_auditoria_acessos;

CREATE POLICY soc_auditor_read_audit
    ON tbl_auditoria_acessos
    FOR SELECT
    TO soc_auditor
    USING (true);


DROP POLICY IF EXISTS soc_pipeline_read_mitre
    ON tbl_mitre_mapping;

CREATE POLICY soc_pipeline_read_mitre
    ON tbl_mitre_mapping
    FOR SELECT
    TO soc_pipeline
    USING (true);


DROP POLICY IF EXISTS threat_intel_writer_insert_mitre
    ON tbl_mitre_mapping;

CREATE POLICY threat_intel_writer_insert_mitre
    ON tbl_mitre_mapping
    FOR INSERT
    TO threat_intel_writer
    WITH CHECK (true);

COMMIT;
