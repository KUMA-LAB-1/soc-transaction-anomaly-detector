-- ============================================================================
-- SCRIPT DE CONSULTAS FORENSES (THREAT HUNTING & AUDITORIA)
-- PROJETO: SECURITY ANALYTICS & THREAT HUNTING BANCÁRIO
-- ============================================================================

-- 🕵️‍♂️ QUERY 1: Identificar Logins com "Viagem Impossível" (Anomalia Geográfica)
-- Busca clientes que logaram de estados diferentes em um curto intervalo de tempo.
SELECT 
    c.id_cliente,
    c.nome_completo,
    l1.localizacao_estimada AS localizacao_original,
    l1.data_hora_acesso AS hora_original,
    l2.localizacao_estimada AS localizacao_suspeita,
    l2.data_hora_acesso AS hora_suspeita,
    l2.endereco_ip AS ip_suspeito,
    l2.dispositivo_modelo AS dispositivo_suspeito
FROM tbl_logs_seguranca l1
JOIN tbl_logs_seguranca l2 ON l1.id_cliente = l2.id_cliente
JOIN tbl_clientes c ON c.id_cliente = l1.id_cliente
WHERE l1.localizacao_estimada <> l2.localizacao_estimada
  AND l2.data_hora_acesso > l1.data_hora_acesso
  AND l2.data_hora_acesso <= l1.data_hora_acesso + INTERVAL '24 hours';


-- 🚨 QUERY 2: Relatório de Alertas Disparados na Madrugada
-- Filtra eventos críticos que geraram alertas de segurança entre 00:00 e 05:00.
SELECT 
    l.data_hora_acesso,
    c.nome_completo,
    l.evento_tipo,
    l.dispositivo_modelo,
    l.localizacao_estimada,
    l.endereco_ip
FROM tbl_logs_seguranca l
JOIN tbl_clientes c ON l.id_cliente = c.id_cliente
WHERE l.status_alerta = TRUE
  AND EXTRACT(HOUR FROM l.data_hora_acesso) BETWEEN 0 AND 5;


-- 💰 QUERY 3: Rastreamento de Transações Suspeitas e Fraudes Fracionadas
-- Identifica movimentações de alto valor ou transações seguidas na mesma conta com status de suspeita ou concluída pós-alerta.
SELECT 
    t.id_transacao,
    c.nome_completo AS titular_conta,
    cont.agencia,
    cont.numero_conta,
    t.tipo_transacao,
    t.valor_transacao,
    t.data_hora_transacao,
    t.status_transacao,
    t.id_dispositivo_origem
FROM tbl_transacoes t
JOIN tbl_contas cont ON t.id_conta_origem = cont.id_conta
JOIN tbl_clientes c ON cont.id_cliente = c.id_cliente
WHERE t.status_transacao IN ('Bloqueada por Suspeita', 'Concluída')
ORDER BY t.data_hora_transacao DESC;
