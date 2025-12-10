-- Migration: Enable Row Level Security (RLS)
-- Descrição: Habilita RLS em todas as tabelas e cria políticas de acesso
-- Data: 2025-12-10
-- IMPORTANTE: Execute em staging primeiro!

-- ============================================
-- FUNÇÕES AUXILIARES
-- ============================================

-- Função para verificar se a request vem do service role
CREATE OR REPLACE FUNCTION is_service_role()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN auth.role() = 'service_role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- HABILITAR RLS EM TODAS AS TABELAS
-- ============================================

-- Pipes
ALTER TABLE pipes ENABLE ROW LEVEL SECURITY;

-- Agencias
ALTER TABLE agencias ENABLE ROW LEVEL SECURITY;

-- Corretores
ALTER TABLE corretores ENABLE ROW LEVEL SECURITY;

-- Usuarios
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- Proprietarios
ALTER TABLE proprietarios ENABLE ROW LEVEL SECURITY;

-- Clientes
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;

-- Imoveis
ALTER TABLE imoveis ENABLE ROW LEVEL SECURITY;

-- Negocios
ALTER TABLE negocios ENABLE ROW LEVEL SECURITY;

-- Atividades
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;

-- Sync State
ALTER TABLE sync_state ENABLE ROW LEVEL SECURITY;

-- ============================================
-- POLÍTICAS DE ACESSO - SERVICE ROLE
-- ============================================

-- Pipes: Service Role - Full Access
CREATE POLICY "Service role full access to pipes"
  ON pipes
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Agencias: Service Role - Full Access
CREATE POLICY "Service role full access to agencias"
  ON agencias
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Corretores: Service Role - Full Access
CREATE POLICY "Service role full access to corretores"
  ON corretores
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Usuarios: Service Role - Full Access
CREATE POLICY "Service role full access to usuarios"
  ON usuarios
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Proprietarios: Service Role - Full Access
CREATE POLICY "Service role full access to proprietarios"
  ON proprietarios
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Clientes: Service Role - Full Access
CREATE POLICY "Service role full access to clientes"
  ON clientes
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Imoveis: Service Role - Full Access
CREATE POLICY "Service role full access to imoveis"
  ON imoveis
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Negocios: Service Role - Full Access
CREATE POLICY "Service role full access to negocios"
  ON negocios
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Atividades: Service Role - Full Access
CREATE POLICY "Service role full access to atividades"
  ON atividades
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- Sync State: Service Role - Full Access
CREATE POLICY "Service role full access to sync_state"
  ON sync_state
  FOR ALL
  USING (is_service_role())
  WITH CHECK (is_service_role());

-- ============================================
-- POLÍTICAS DE ACESSO - PÚBLICO (READ-ONLY)
-- ============================================
-- IMPORTANTE: Descomente apenas se precisar de acesso público
-- Por padrão, todas as tabelas estão bloqueadas para acesso público

-- Exemplo de política READ-ONLY para dashboards públicos:
-- CREATE POLICY "Public read access to imoveis"
--   ON imoveis
--   FOR SELECT
--   USING (true);

-- ============================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- ============================================

COMMENT ON FUNCTION is_service_role() IS 'Verifica se a request atual vem do service role (ETL)';

COMMENT ON POLICY "Service role full access to clientes" ON clientes IS 'Permite acesso completo ao service role para operações de ETL';

-- ============================================
-- VERIFICAÇÃO
-- ============================================

-- Para verificar se RLS está habilitado:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Para listar políticas:
-- SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname = 'public';
