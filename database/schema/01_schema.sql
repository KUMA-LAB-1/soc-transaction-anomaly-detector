-- ============================================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS (SCHEMA)
-- PROJETO: SECURITY ANALYTICS & THREAT HUNTING BANCÁRIO
-- BANCO DE DADOS ALVO: POSTGRESQL
-- ============================================================================

-- 1. TABELA DE CLIENTES
-- Armazena os dados cadastrais dos clientes (Alvo prioritário de vazamentos/LGPD)
CREATE TABLE tbl_clientes (
    id_cliente SERIAL PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELA DE CONTAS BANCÁRIAS
-- Padrão Bradesco: Agência com 4 dígitos e Conta Corrente/Poupança com DV
CREATE TABLE tbl_contas (
    id_conta SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES tbl_clientes(id_cliente) ON DELETE CASCADE,
    agencia VARCHAR(4) NOT NULL,
    numero_conta VARCHAR(10) NOT NULL,
    digito_verificador VARCHAR(2) NOT NULL,
    tipo_conta VARCHAR(20) CHECK (tipo_conta IN ('Corrente', 'Poupança', 'Salário')),
    saldo_atual NUMERIC(15, 2) DEFAULT 0.00,
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TABELA DE TRANSAÇÕES FINANCEIRAS
-- Registra o fluxo financeiro (Onde buscaremos anomalias de valores e horários)
CREATE TABLE tbl_transacoes (
    id_transacao SERIAL PRIMARY KEY,
    id_conta_origem INT REFERENCES tbl_contas(id_conta),
    tipo_transacao VARCHAR(20) CHECK (tipo_transacao IN ('Pix', 'TED', 'DOC', 'Cartão Virtual')),
    valor_transacao NUMERIC(15, 2) NOT NULL,
    data_hora_transacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_dispositivo_origem VARCHAR(100) NOT NULL, -- UUID ou IMEI do celular que enviou
    status_transacao VARCHAR(30) CHECK (status_transacao IN ('Concluída', 'Em Análise', 'Bloqueada por Suspeita'))
);

-- 4. TABELA DE LOGS DE ACESSO E SEGURANÇA
-- A tabela-chave da perícia forense. Aqui registraremos os IPs, logins e falhas de autenticação.
CREATE TABLE tbl_logs_seguranca (
    id_log SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES tbl_clientes(id_cliente) ON DELETE SET NULL,
    data_hora_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endereco_ip VARCHAR(45) NOT NULL,          -- Suporta IPv4 e IPv6
    dispositivo_modelo VARCHAR(100),           -- Ex: iPhone 14, Samsung S23, Web/Chrome
    localizacao_estimada VARCHAR(100),         -- Ex: São Paulo - SP, Buenos Aires - AR
    evento_tipo VARCHAR(50) CHECK (evento_tipo IN (
        'Login Sucesso', 'Falha de Senha', 'Bloqueio de Conta', 
        'Dispositivo Novo Vinculado', 'Alteração de Limite Pix'
    )),
    status_alerta BOOLEAN DEFAULT FALSE        -- TRUE se o sistema de segurança disparou alerta
);
