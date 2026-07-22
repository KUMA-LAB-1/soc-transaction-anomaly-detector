BEGIN;

-- ============================================================================
-- INJEÇÃO DE +500 TRANSAÇÕES E LOGS ANÔMALOS (LOTE MASSIVO RANDÔMICO)
-- ============================================================================
DO $$
DECLARE
    v_conta RECORD;
    v_i INT := 1;
    v_id_transacao INT;
    v_valor_anomalo NUMERIC;
    v_hora_madrugada TIMESTAMP;
    v_ip_suspeito TEXT;
    v_dispositivo_novo TEXT;
    v_vetor_ataque INT;
BEGIN
    -- Loop para gerar 500 registros randômicos adicionais (IDs de 201 a 700)
    FOR v_i IN 201..700 LOOP
        
        -- Seleciona uma conta de forma estocástica
        SELECT id_conta, id_cliente 
        INTO v_conta 
        FROM tbl_contas 
        ORDER BY random() 
        LIMIT 1;

        -- Variância ampla de valores altos (R$ 15.000 a R$ 120.000)
        v_valor_anomalo := ROUND((15000 + (random() ^ 1.8) * 105000)::numeric, 2);
        
        -- Sorteia data/hora nos últimos 60 dias (com foco em horários de risco)
        v_hora_madrugada := (CURRENT_TIMESTAMP - (random() * INTERVAL '60 days'))::date 
                            + (INTERVAL '1 hour' * floor(random() * 24)::int) 
                            + (INTERVAL '1 minute' * floor(random() * 59)::int);

        -- Pool expandido de IPs maliciosos / IPs de infraestrutura de borda
        v_ip_suspeito := (ARRAY[
            '185.220.101.5',   '45.154.255.12',   '193.142.146.210', 
            '185.191.171.10',  '109.236.87.19',   '185.220.102.8',   
            '194.26.29.112',   '45.142.214.50',   '193.37.252.19',   
            '191.101.31.88',   '212.102.35.15',   '185.156.177.20'
        ])[1 + floor(random() * 12)::int];

        v_dispositivo_novo := 'DEV-RANDOM-' || UPPER(SUBSTRING(md5(v_i::text) FROM 1 FOR 6));

        -- 1. Injeta Transação Anômala
        INSERT INTO tbl_transacoes (
            id_conta_origem,
            tipo_transacao,
            valor_transacao,
            data_hora_transacao,
            status_transacao,
            id_dispositivo_origem
        )
        VALUES (
            v_conta.id_conta,
            (ARRAY['Pix', 'TED', 'Cartão Virtual'])[1 + floor(random() * 3)::int],
            v_valor_anomalo,
            v_hora_madrugada,
            (ARRAY['Em Análise', 'Bloqueada por Suspeita'])[1 + floor(random() * 2)::int],
            v_dispositivo_novo
        )
        RETURNING id_transacao INTO v_id_transacao;

        -- Sorteia um dos 4 perfis comportamentais de forma puramente randômica (1 a 4)
        v_vetor_ataque := 1 + floor(random() * 4)::int;

        -- 2. Injeta Sequência de Logs Comportamentais (Seguindo estrictamente o CHECK)
        IF v_vetor_ataque = 1 THEN
            -- Perfil 1: Brute Force seguido de Acesso
            INSERT INTO tbl_logs_seguranca (id_cliente, data_hora_acesso, endereco_ip, dispositivo_modelo, localizacao_estimada, evento_tipo, status_alerta)
            VALUES 
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '15 minutes', v_ip_suspeito, 'Custom Python Script', 'Reykjavik, IS', 'Falha de Senha', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '10 minutes', v_ip_suspeito, 'Custom Python Script', 'Reykjavik, IS', 'Falha de Senha', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '2 minutes',  v_ip_suspeito, 'Custom Python Script', 'Reykjavik, IS', 'Login Sucesso', TRUE);

        ELSIF v_vetor_ataque = 2 THEN
            -- Perfil 2: Account Takeover (Novo Dispositivo + Limite)
            INSERT INTO tbl_logs_seguranca (id_cliente, data_hora_acesso, endereco_ip, dispositivo_modelo, localizacao_estimada, evento_tipo, status_alerta)
            VALUES 
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '20 minutes', v_ip_suspeito, 'Unknown Linux Mobile', 'Panama City, PA', 'Dispositivo Novo Vinculado', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '12 minutes', v_ip_suspeito, 'Unknown Linux Mobile', 'Panama City, PA', 'Alteração de Limite Pix', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '1 minute',  v_ip_suspeito, 'Unknown Linux Mobile', 'Panama City, PA', 'Login Sucesso', TRUE);

        ELSIF v_vetor_ataque = 3 THEN
            -- Perfil 3: Mudança de Limite e Validação em Sessão Suspeita
            INSERT INTO tbl_logs_seguranca (id_cliente, data_hora_acesso, endereco_ip, dispositivo_modelo, localizacao_estimada, evento_tipo, status_alerta)
            VALUES 
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '30 minutes', v_ip_suspeito, 'Headless Browser', 'Zurich, CH', 'Login Sucesso', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '5 minutes',  v_ip_suspeito, 'Headless Browser', 'Zurich, CH', 'Alteração de Limite Pix', TRUE);

        ELSE
            -- Perfil 4: Escalação Rápida com Falhas Intercaladas
            INSERT INTO tbl_logs_seguranca (id_cliente, data_hora_acesso, endereco_ip, dispositivo_modelo, localizacao_estimada, evento_tipo, status_alerta)
            VALUES 
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '25 minutes', v_ip_suspeito, 'Botnet HTTP Client', 'Sofia, BG', 'Falha de Senha', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '18 minutes', v_ip_suspeito, 'Botnet HTTP Client', 'Sofia, BG', 'Dispositivo Novo Vinculado', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '8 minutes',  v_ip_suspeito, 'Botnet HTTP Client', 'Sofia, BG', 'Alteração de Limite Pix', TRUE),
                (v_conta.id_cliente, v_hora_madrugada - INTERVAL '1 minute',  v_ip_suspeito, 'Botnet HTTP Client', 'Sofia, BG', 'Login Sucesso', TRUE);
            
        END IF;

    END LOOP;
END $$;

COMMIT;
