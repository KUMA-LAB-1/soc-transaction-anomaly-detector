BEGIN;

INSERT INTO tbl_clientes (
    cliente_pseudonimo,
    nome_completo,
    cpf,
    telefone
)
VALUES
    (
        '10000000-0000-4000-8000-000000000001',
        'Cliente Sintético 001',
        '000.000.001-00',
        '(00) 90000-0001'
    ),
    (
        '10000000-0000-4000-8000-000000000002',
        'Cliente Sintético 002',
        '000.000.002-00',
        '(00) 90000-0002'
    ),
    (
        '10000000-0000-4000-8000-000000000003',
        'Cliente Sintético 003',
        '000.000.003-00',
        '(00) 90000-0003'
    ),
    (
        '10000000-0000-4000-8000-000000000004',
        'Cliente Sintético 004',
        '000.000.004-00',
        '(00) 90000-0004'
    ),
    (
        '10000000-0000-4000-8000-000000000005',
        'Cliente Sintético 005',
        '000.000.005-00',
        '(00) 90000-0005'
    )
ON CONFLICT (cpf) DO NOTHING;

INSERT INTO tbl_contas (
    id_cliente,
    agencia,
    numero_conta,
    digito_verificador,
    tipo_conta,
    saldo_atual
)
SELECT
    c.id_cliente,
    dados.agencia,
    dados.numero_conta,
    dados.digito_verificador,
    dados.tipo_conta,
    dados.saldo_atual
FROM (
    VALUES
        ('000.000.001-00', '1001', '000000001', '1', 'Corrente', 25000.00::numeric),
        ('000.000.002-00', '1001', '000000002', '2', 'Corrente', 18000.00::numeric),
        ('000.000.003-00', '1002', '000000003', '3', 'Poupança', 32000.00::numeric),
        ('000.000.004-00', '1002', '000000004', '4', 'Corrente', 45000.00::numeric),
        ('000.000.005-00', '1003', '000000005', '5', 'Poupança', 12000.00::numeric)
) AS dados(
    cpf,
    agencia,
    numero_conta,
    digito_verificador,
    tipo_conta,
    saldo_atual
)
JOIN tbl_clientes c
    ON c.cpf = dados.cpf
WHERE NOT EXISTS (
    SELECT 1
    FROM tbl_contas existente
    WHERE existente.id_cliente = c.id_cliente
      AND existente.agencia = dados.agencia
      AND existente.numero_conta = dados.numero_conta
);

COMMIT;