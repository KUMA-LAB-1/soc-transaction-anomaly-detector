-- ============================================================================
-- HARDENING DE SEGURANÇA + CORRELAÇÃO LOGS x TRANSAÇÕES (THREAT HUNTING)
-- Aplique depois dos scripts 01-07 já existentes.
-- ============================================================================

-- 0. Extensão necessária para hashing/pseudonimização (nativa no Supabase)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------------------------------------------------------
-- 1. VIEW REDEFINIDA: pseudonimização real (não reversível por inspeção) +
--    mascaramento de conta + sinais correlacionados de tbl_logs_seguranca.
--
--    ATENÇÃO: troque 'TROQUE_ESTE_PEPPER_SECRETO' por um valor secreto seu,
--    guardado fora do controle de versão (idealmente via
--    ALTER DATABASE seu_banco SET app.pepper = 'valor-secreto';
--    e troque a literal abaixo por current_setting('app.pepper', true)).
--    Deixei como literal aqui só para simplificar o teste.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_analise_investigacao_soc AS
SELECT
    c.id_cliente,

    -- Pseudônimo estável e NÃO reversível por inspeção visual (era "Carlos E."
    -- antes, que combinado com agência/conta permitia reidentificação trivial)
    'CLI-' || UPPER(SUBSTRING(
        encode(digest(c.id_cliente::text || 'TROQUE_ESTE_PEPPER_SECRETO', 'sha256'), 'hex')
        FROM 1 FOR 8
    )) AS cliente_pseudonimo,

    -- CPF: nenhum dígito real exposto nesta view de investigação de rotina
    '***.***.***-**' AS cpf_protegido,

    cont.agencia,
    -- Só os 4 últimos dígitos da conta (evita reidentificação cruzando com
    -- vazamentos externos que contenham conta completa + nome)
    RIGHT(cont.numero_conta, 4) AS numero_conta_mascarado,

    t.id_transacao,
    t.tipo_transacao,
    t.valor_transacao,
    t.data_hora_transacao,
    t.status_transacao,
    t.id_dispositivo_origem,

    -- ---- SINAIS CORRELACIONADOS (para features de ML e para o MITRE lookup) ----
    COALESCE(logs.falhas_login_recentes, 0) AS falhas_login_recentes,
    COALESCE(logs.dispositivo_novo_flag, FALSE) AS dispositivo_novo_flag,
    COALESCE(logs.alteracao_limite_flag, FALSE) AS alteracao_limite_flag,
    COALESCE(logs.localizacoes_distintas_recentes, 0) > 1 AS mudanca_localizacao_flag

FROM tbl_transacoes t
JOIN tbl_contas cont ON t.id_conta_origem = cont.id_conta
JOIN tbl_clientes c ON cont.id_cliente = c.id_cliente
LEFT JOIN LATERAL (
    SELECT
        COUNT(*) FILTER (WHERE l.evento_tipo = 'Falha de Senha')          AS falhas_login_recentes,
        BOOL_OR(l.evento_tipo = 'Dispositivo Novo Vinculado')             AS dispositivo_novo_flag,
        BOOL_OR(l.evento_tipo = 'Alteração de Limite Pix')                AS alteracao_limite_flag,
        COUNT(DISTINCT l.localizacao_estimada)                           AS localizacoes_distintas_recentes
    FROM tbl_logs_seguranca l
    WHERE l.id_cliente = c.id_cliente
      -- janela de correlação: eventos de log até 2h ANTES da transação
      -- (causal: nunca olha eventos futuros em relação à transação)
      AND l.data_hora_acesso BETWEEN t.data_hora_transacao - INTERVAL '2 hours'
                                  AND t.data_hora_transacao
) logs ON TRUE;

COMMENT ON VIEW v_analise_investigacao_soc IS
    'View de investigação para o SOC. Pseudonimização não-reversível por '
    'inspeção + sinais de correlação com tbl_logs_seguranca para threat hunting. '
    'Analistas/serviços de rotina devem usar SOMENTE esta view — acesso direto '
    'a tbl_clientes/tbl_transacoes/tbl_logs_seguranca deve ficar restrito a um '
    'papel de auditoria com justificativa registrada (ver tbl_auditoria_acessos).';


-- ----------------------------------------------------------------------------
-- 2. TABELA DE AUDITORIA DE ACESSO (accountability - LGPD art. 6º, X)
--    Toda execução do pipeline registra quem rodou, quando e quantas linhas
--    de dados sensíveis foram lidas.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_auditoria_acessos (
    id_auditoria SERIAL PRIMARY KEY,
    usuario_execucao VARCHAR(100) NOT NULL,
    view_ou_tabela_acessada VARCHAR(100) NOT NULL,
    qtd_linhas_retornadas INT,
    executado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalidade TEXT
);

ALTER TABLE tbl_auditoria_acessos ENABLE ROW LEVEL SECURITY;
CREATE POLICY admin_full_access_auditoria ON tbl_auditoria_acessos
    TO service_role USING (true);


-- [ ] Considere criptografar o CPF em repouso com pgcrypto
--     (pgp_sym_encrypt na escrita / pgp_sym_decrypt só em rotina de auditoria
--     legal explícita), em vez de manter em texto puro em tbl_clientes.
-- ============================================================================
