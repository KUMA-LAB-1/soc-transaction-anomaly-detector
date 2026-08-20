-- ============================================================================
-- PRIVILEGED FORENSIC INVESTIGATION QUERIES
-- Security Analytics & Threat Hunting Banking Lab
-- ============================================================================
--
-- These queries are intended for manual, privileged incident investigation.
-- They are NOT consumed by the normal SOC detection pipeline.
--
-- Raw security attributes such as IP address, device information and estimated
-- location are exposed only where they provide forensic value.
--
-- Access to the underlying operational tables must be granted separately
-- through an explicitly authorized forensic role.
--
-- All queries in this file are read-only.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. RAPID GEOGRAPHIC CHANGE INVESTIGATION
--
-- Compares each security event with the immediately preceding event associated
-- with the same customer and identifies location changes within 24 hours.
--
-- This is an investigative signal only. It does NOT prove impossible travel,
-- because geographic distance and feasible travel time are not calculated.
-- ----------------------------------------------------------------------------

WITH eventos_ordenados AS (
    SELECT
        c.cliente_pseudonimo,
        l.data_hora_acesso,
        l.localizacao_estimada,
        l.endereco_ip,
        l.dispositivo_modelo,

        LAG(l.data_hora_acesso) OVER (
            PARTITION BY l.id_cliente
            ORDER BY l.data_hora_acesso, l.id_log
        ) AS evento_anterior_em,

        LAG(l.localizacao_estimada) OVER (
            PARTITION BY l.id_cliente
            ORDER BY l.data_hora_acesso, l.id_log
        ) AS localizacao_anterior

    FROM tbl_logs_seguranca AS l
    JOIN tbl_clientes AS c
        ON c.id_cliente = l.id_cliente
)

SELECT
    cliente_pseudonimo,
    evento_anterior_em,
    localizacao_anterior,
    data_hora_acesso AS evento_posterior_em,
    localizacao_estimada AS localizacao_posterior,
    endereco_ip AS endereco_ip_posterior,
    dispositivo_modelo AS dispositivo_posterior
FROM eventos_ordenados
WHERE evento_anterior_em IS NOT NULL
  AND localizacao_anterior IS NOT NULL
  AND localizacao_estimada IS NOT NULL
  AND localizacao_anterior <> localizacao_estimada
  AND data_hora_acesso
      <= evento_anterior_em + INTERVAL '24 hours'
ORDER BY
    cliente_pseudonimo,
    evento_anterior_em,
    data_hora_acesso;


-- ----------------------------------------------------------------------------
-- 2. SECURITY ALERTS DURING UNUSUAL HOURS
--
-- Reviews security events explicitly marked as alerts between midnight and
-- 05:59. Customer identity remains pseudonymized while operational evidence
-- required for investigation is retained.
-- ----------------------------------------------------------------------------

SELECT
    c.cliente_pseudonimo,
    l.data_hora_acesso,
    l.evento_tipo,
    l.dispositivo_modelo,
    l.localizacao_estimada,
    l.endereco_ip
FROM tbl_logs_seguranca AS l
JOIN tbl_clientes AS c
    ON c.id_cliente = l.id_cliente
WHERE l.status_alerta IS TRUE
  AND EXTRACT(HOUR FROM l.data_hora_acesso) BETWEEN 0 AND 5
ORDER BY
    l.data_hora_acesso DESC,
    c.cliente_pseudonimo;


-- ----------------------------------------------------------------------------
-- 3. SUSPICIOUS TRANSACTION INVESTIGATION
--
-- Reviews transactions whose historical status indicates a suspicious or
-- analytically relevant outcome. Direct customer identity and full account
-- number are intentionally excluded.
-- ----------------------------------------------------------------------------

SELECT
    c.cliente_pseudonimo,
    t.id_transacao,
    t.tipo_transacao,
    t.valor_transacao,
    t.data_hora_transacao,
    t.status_transacao,
    RIGHT(cont.numero_conta, 4) AS conta_ultimos_quatro,
    t.id_dispositivo_origem
FROM tbl_transacoes AS t
JOIN tbl_contas AS cont
    ON cont.id_conta = t.id_conta_origem
JOIN tbl_clientes AS c
    ON c.id_cliente = cont.id_cliente
WHERE t.status_transacao IN (
    'Bloqueada por Suspeita',
    'Concluída'
)
ORDER BY
    t.data_hora_transacao DESC,
    t.id_transacao DESC;
