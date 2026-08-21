-- ============================================================================
-- SOC INVESTIGATION VIEW
-- Dataset mínimo e pseudonimizado consumido pelo pipeline de detecção.
-- ============================================================================

CREATE OR REPLACE VIEW v_analise_investigacao_soc
WITH (security_invoker = true) AS
SELECT
    c.cliente_pseudonimo,
    t.id_transacao,
    t.tipo_transacao,
    t.valor_transacao,
    t.data_hora_transacao,
    t.status_transacao,

    COALESCE(logs.falhas_login_recentes, 0) AS falhas_login_recentes,
    COALESCE(logs.dispositivo_novo_flag, FALSE) AS dispositivo_novo_flag,
    COALESCE(logs.alteracao_limite_flag, FALSE) AS alteracao_limite_flag,
    COALESCE(logs.localizacoes_distintas_recentes, 0) > 1
        AS mudanca_localizacao_flag

FROM tbl_transacoes AS t

JOIN tbl_contas AS cont
    ON cont.id_conta = t.id_conta_origem

JOIN tbl_clientes AS c
    ON c.id_cliente = cont.id_cliente

LEFT JOIN LATERAL (
    SELECT
        COUNT(*) FILTER (
            WHERE l.evento_tipo = 'Falha de Senha'
        ) AS falhas_login_recentes,

        BOOL_OR(
            l.evento_tipo = 'Dispositivo Novo Vinculado'
        ) AS dispositivo_novo_flag,

        BOOL_OR(
            l.evento_tipo = 'Alteração de Limite Pix'
        ) AS alteracao_limite_flag,

        COUNT(DISTINCT l.localizacao_estimada)
            AS localizacoes_distintas_recentes

    FROM tbl_logs_seguranca AS l

    WHERE l.id_cliente = c.id_cliente
      AND l.data_hora_acesso
          BETWEEN t.data_hora_transacao - INTERVAL '2 hours'
              AND t.data_hora_transacao
) AS logs ON TRUE;

COMMENT ON VIEW v_analise_investigacao_soc IS
    'Dataset pseudonimizado e minimizado utilizado pelo pipeline SOC. '
    'A view expõe somente atributos necessários à análise de transações '
    'e sinais derivados da correlação temporal com eventos de segurança.';
