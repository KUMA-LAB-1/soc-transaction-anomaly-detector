-- ============================================================================
-- AUDIT SCHEMA
-- Registro de acessos realizados pelo pipeline SOC.
-- ============================================================================

CREATE TABLE tbl_auditoria_acessos (
    id_auditoria SERIAL PRIMARY KEY,
    usuario_execucao VARCHAR(100) NOT NULL,
    view_ou_tabela_acessada VARCHAR(100) NOT NULL,
    qtd_linhas_retornadas INT,
    executado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalidade TEXT,

    CONSTRAINT ck_tbl_auditoria_qtd_linhas
        CHECK (
            qtd_linhas_retornadas IS NULL
            OR qtd_linhas_retornadas >= 0
        )
);

CREATE INDEX idx_tbl_auditoria_executado_em
    ON tbl_auditoria_acessos (executado_em);

CREATE INDEX idx_tbl_auditoria_usuario_execucao
    ON tbl_auditoria_acessos (usuario_execucao);