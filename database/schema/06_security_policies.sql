-- ============================================================================
-- SCRIPT DE POLÍTICAS DE SEGURANÇA (ROW LEVEL SECURITY - RLS)
-- PROJETO: SECURITY ANALYTICS & THREAT HUNTING BANCÁRIO
-- ============================================================================

-- 1. Habilitando o RLS em todas as tabelas (Bloqueio total por padrão)
ALTER TABLE tbl_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_contas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tbl_logs_seguranca ENABLE ROW LEVEL SECURITY;

-- 2. Criando políticas de acesso restrito
-- Garante que apenas usuários administradores/sistemas de auditoria internos (Service Role) acessem os dados
CREATE POLICY admin_full_access_clientes ON tbl_clientes TO service_role USING (true);
CREATE POLICY admin_full_access_contas ON tbl_contas TO service_role USING (true);
CREATE POLICY admin_full_access_transacoes ON tbl_transacoes TO service_role USING (true);
CREATE POLICY admin_full_access_logs ON tbl_logs_seguranca TO service_role USING (true);
