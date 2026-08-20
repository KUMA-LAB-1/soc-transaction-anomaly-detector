-- ============================================================================
-- CORE DATABASE SCHEMA
-- PROJETO: SECURITY ANALYTICS & THREAT HUNTING BANCÁRIO
-- BANCO DE DADOS ALVO: POSTGRESQL
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CLIENTES
-- Dados sintéticos utilizados para representar entidades bancárias no laboratório.
-- ----------------------------------------------------------------------------
CREATE TABLE tbl_clientes (
    id_cliente SERIAL PRIMARY KEY,
    cliente_pseudonimo UUID NOT NULL DEFAULT gen_random_uuid(),
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_tbl_clientes_pseudonimo
        UNIQUE (cliente_pseudonimo),

    CONSTRAINT uq_tbl_clientes_cpf
        UNIQUE (cpf)
);


-- ----------------------------------------------------------------------------
-- 2. CONTAS
-- Cada conta pertence obrigatoriamente a um cliente.
-- ----------------------------------------------------------------------------
CREATE TABLE tbl_contas (
    id_conta SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL,
    agencia VARCHAR(4) NOT NULL,
    numero_conta VARCHAR(10) NOT NULL,
    digito_verificador VARCHAR(2) NOT NULL,
    tipo_conta VARCHAR(20) NOT NULL,
    saldo_atual NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tbl_contas_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES tbl_clientes(id_cliente)
        ON DELETE RESTRICT,

    CONSTRAINT ck_tbl_contas_tipo
        CHECK (tipo_conta IN ('Corrente', 'Poupança', 'Salário')),

    CONSTRAINT uq_tbl_contas_identidade
        UNIQUE (agencia, numero_conta, digito_verificador)
);


-- ----------------------------------------------------------------------------
-- 3. TRANSAÇÕES
-- Eventos financeiros analisados pelo pipeline SOC.
-- ----------------------------------------------------------------------------
CREATE TABLE tbl_transacoes (
    id_transacao SERIAL PRIMARY KEY,
    id_conta_origem INT NOT NULL,
    tipo_transacao VARCHAR(20) NOT NULL,
    valor_transacao NUMERIC(15, 2) NOT NULL,
    data_hora_transacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_dispositivo_origem VARCHAR(100) NOT NULL,
    status_transacao VARCHAR(30) NOT NULL,

    CONSTRAINT fk_tbl_transacoes_conta_origem
        FOREIGN KEY (id_conta_origem)
        REFERENCES tbl_contas(id_conta),
        ON DELETE RESTRICT,

    CONSTRAINT ck_tbl_transacoes_tipo
        CHECK (
            tipo_transacao IN (
                'Pix',
                'TED',
                'DOC',
                'Cartão Virtual'
            )
        ),

    CONSTRAINT ck_tbl_transacoes_valor_positivo
        CHECK (valor_transacao > 0),

    CONSTRAINT ck_tbl_transacoes_status
        CHECK (
            status_transacao IN (
                'Concluída',
                'Em Análise',
                'Bloqueada por Suspeita'
            )
        )
);


-- ----------------------------------------------------------------------------
-- 4. LOGS DE SEGURANÇA
-- Eventos utilizados para correlação temporal e threat hunting.
-- ----------------------------------------------------------------------------
CREATE TABLE tbl_logs_seguranca (
    id_log SERIAL PRIMARY KEY,
    id_cliente INT,
    data_hora_acesso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endereco_ip VARCHAR(45) NOT NULL,
    dispositivo_modelo VARCHAR(100),
    localizacao_estimada VARCHAR(100),
    evento_tipo VARCHAR(50) NOT NULL,
    status_alerta BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_tbl_logs_seguranca_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES tbl_clientes(id_cliente)
        ON DELETE SET NULL,

    CONSTRAINT ck_tbl_logs_seguranca_evento
        CHECK (
            evento_tipo IN (
                'Login Sucesso',
                'Falha de Senha',
                'Bloqueio de Conta',
                'Dispositivo Novo Vinculado',
                'Alteração de Limite Pix'
            )
        )
);


-- ----------------------------------------------------------------------------
-- 5. ÍNDICES OPERACIONAIS
-- Suportam joins e correlação temporal utilizados pelo pipeline SOC.
-- ----------------------------------------------------------------------------

CREATE INDEX idx_tbl_contas_id_cliente
    ON tbl_contas (id_cliente);

CREATE INDEX idx_tbl_transacoes_conta_data
    ON tbl_transacoes (id_conta_origem, data_hora_transacao);

CREATE INDEX idx_tbl_logs_cliente_data
    ON tbl_logs_seguranca (id_cliente, data_hora_acesso);
