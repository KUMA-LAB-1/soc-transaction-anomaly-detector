-- ============================================================================
-- MODELO 1: ETL VIA BANCO DE DADOS (CRIAÇÃO DE VIEW SEGURA - LGPD)
-- ============================================================================

CREATE OR REPLACE VIEW v_analise_investigacao_soc AS
SELECT 
    -- 1. Mantemos o ID para tracking interno, mas ocultamos informações pessoais diretas
    c.id_cliente,
    
    -- 2. Transformação (Mascaramento de Nome): Exibe apenas o primeiro nome e a inicial do sobrenome
    -- Exemplo: "Carlos Eduardo Silva" vira "Carlos E."
    SPLIT_PART(c.nome_completo, ' ', 1) || ' ' || 
    SUBSTRING(SPLIT_PART(c.nome_completo, ' ', 2) FROM 1 FOR 1) || '.' AS cliente_anonimizado,
    
    -- 3. Transformação (Mascaramento de CPF): Exibe apenas os dígitos centrais para auditoria
    -- Exemplo: "123.456.789-00" vira "***.456.789-**"
    '***.' || SUBSTRING(c.cpf FROM 5 FOR 7) || '-**' AS cpf_protegido,
    
    -- 4. Dados operacionais e financeiros trazidos via JOIN para a análise do SOC
    cont.agencia,
    cont.numero_conta,
    t.tipo_transacao,
    t.valor_transacao,
    t.data_hora_transacao,
    t.status_transacao,
    t.id_dispositivo_origem
FROM tbl_transacoes t
JOIN tbl_contas cont ON t.id_conta_origem = cont.id_conta
JOIN tbl_clientes c ON cont.id_cliente = c.id_cliente;
