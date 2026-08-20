-- ============================================================================
-- DATABASE SECURITY
-- Roles, privileges and Row Level Security for the SOC data platform.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. AUTHORIZATION ROLES
-- NOLOGIN roles represent capabilities only.
-- Runtime identities must be associated with these roles outside this repository.
-- ----------------------------------------------------------------------------

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
-- Explicitly remove access inherited through PostgreSQL's PUBLIC role.
-- ----------------------------------------------------------------------------

REVOKE ALL ON TABLE tbl_clientes FROM PUBLIC;
REVOKE ALL ON TABLE tbl_contas FROM PUBLIC;
REVOKE ALL ON TABLE tbl_transacoes FROM PUBLIC;
REVOKE ALL ON TABLE tbl_logs_seguranca FROM PUBLIC;
REVOKE ALL ON TABLE tbl_auditoria_acessos FROM PUBLIC;
REVOKE ALL ON TABLE tbl_mitre_mapping FROM PUBLIC;
REVOKE ALL ON TABLE v_analise_investigacao_soc FROM PUBLIC;
REVOKE ALL
    ON SEQUENCE tbl_auditoria_acessos_id_auditoria_seq
    FROM PUBLIC;


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
-- 7. AUDIT RLS POLICIES
-- Operational pipelines may append audit records but cannot inspect or modify
-- historical audit data. Auditors receive read-only visibility.
-- ----------------------------------------------------------------------------

CREATE POLICY soc_pipeline_insert_audit
    ON tbl_auditoria_acessos
    FOR INSERT
    TO soc_pipeline
    WITH CHECK (true);

CREATE POLICY soc_auditor_read_audit
    ON tbl_auditoria_acessos
    FOR SELECT
    TO soc_auditor
    USING (true);

CREATE POLICY soc_pipeline_read_mitre
    ON tbl_mitre_mapping
    FOR SELECT
    TO soc_pipeline
    USING (true);

CREATE POLICY threat_intel_writer_insert_mitre
    ON tbl_mitre_mapping
    FOR INSERT
    TO threat_intel_writer
    WITH CHECK (true);