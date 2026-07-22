BEGIN;

-- ============================================================================
-- INJEÇÃO DE 1.000 TRANSAÇÕES E LOGS TIPO BASELINE (COMPATÍVEL COM O SCHEMA)
-- ============================================================================
DO $$
DECLARE
    v_conta RECORD;
    v_i INT;
    v_id_transacao INT;
    v_valor_normal NUMERIC;
    v_hora_normal TIMESTAMP;
    v_ip_legitimo TEXT;
    v_dispositivo_legitimo TEXT;
BEGIN
    FOR v_i IN 1..1000 LOOP
        
        -- Seleciona uma das contas existentes para associar o movimento
        SELECT c.id_conta, c.id_cliente 
        INTO v_conta 
        FROM tbl_contas c
        ORDER BY random() 
        LIMIT 1;

        -- Valores comuns do dia a dia (R$ 15,00 a R$ 450,00)
        v_valor_normal := ROUND((15 + (random() ^ 2) * 435)::numeric, 2);
        
        -- Janela temporal diurna (entre 08:00 e 21:00) nos últimos 60 dias
        v_hora_normal := (CURRENT_TIMESTAMP - (random() * INTERVAL '60 days'))::date 
                         + (INTERVAL '8 hours' + (random() * INTERVAL '13 hours'));

        -- IPs locais/domésticos do padrão da base legítima
        v_ip_legitimo := '192.168.1.' || (10 + floor(random() * 200)::int);

        -- Modelos de dispositivos do padrão da base
        v_dispositivo_legitimo := (ARRAY[
            'iPhone 13', 
            'Samsung Galaxy S22', 
            'Xiaomi Redmi Note 11', 
            'Motorola Edge 30'
        ])[1 + floor(random() * 4)::int];

        -- 1. Injeta Transação Normal (Status 'Concluída')
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
            (ARRAY['Pix', 'TED', 'DOC', 'Cartão Virtual'])[1 + floor(random() * 4)::int],
            v_valor_normal,
            v_hora_normal,
            'Concluída',
            'DEV-MOB-' || UPPER(SUBSTRING(md5(v_conta.id_conta::text) FROM 1 FOR 8))
        )
        RETURNING id_transacao INTO v_id_transacao;

        -- 2. Injeta Log de Segurança Normal (Login Sucesso e Alerta Falso)
        INSERT INTO tbl_logs_seguranca (
            id_cliente,
            data_hora_acesso,
            endereco_ip,
            dispositivo_modelo,
            localizacao_estimada,
            evento_tipo,
            status_alerta
        )
        VALUES (
            v_conta.id_cliente,
            v_hora_normal - (INTERVAL '1 minute' * (1 + floor(random() * 10)::int)),
            v_ip_legitimo,
            v_dispositivo_legitimo,
            'São Paulo, BR',
            'Login Sucesso',
            FALSE
        );

    END LOOP;
END $$;

COMMIT;
