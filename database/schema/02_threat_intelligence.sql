-- ============================================================================
-- THREAT INTELLIGENCE SCHEMA
-- MITRE ATT&CK mapping utilizado pelo pipeline SOC
-- ============================================================================

CREATE TABLE IF NOT EXISTS tbl_mitre_mapping (
    mitre_id VARCHAR(15) NOT NULL,
    mitre_tecnica VARCHAR(200) NOT NULL,
    mitre_tatica VARCHAR(150) NOT NULL,
    descricao TEXT,
    procedimentos TEXT,

    CONSTRAINT pk_tbl_mitre_mapping
        PRIMARY KEY (mitre_id, mitre_tatica)
);

COMMENT ON TABLE tbl_mitre_mapping IS
    'Mapeamento MITRE ATT&CK utilizado para enriquecimento de alertas e análise SOC.';

COMMENT ON COLUMN tbl_mitre_mapping.mitre_id IS
    'Identificador oficial da técnica MITRE ATT&CK, por exemplo T1110.';

COMMENT ON COLUMN tbl_mitre_mapping.mitre_tatica IS
    'Tática MITRE ATT&CK associada à técnica.';