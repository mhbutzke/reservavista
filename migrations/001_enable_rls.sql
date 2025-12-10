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
ALTER TABLE IF EXISTS pipes ENABLE ROW LEVEL SECURITY;

-- Agencias
ALTER TABLE IF EXISTS agencias ENABLE ROW LEVEL SECURITY;

-- Corretores
ALTER TABLE IF EXISTS corretores ENABLE ROW LEVEL SECURITY;

-- Usuarios
ALTER TABLE IF EXISTS usuarios ENABLE ROW LEVEL SECURITY;

-- Proprietarios
ALTER TABLE IF EXISTS proprietarios ENABLE ROW LEVEL SECURITY;

-- Clientes
ALTER TABLE IF EXISTS clientes ENABLE ROW LEVEL SECURITY;

-- Imoveis
ALTER TABLE IF EXISTS imoveis ENABLE ROW LEVEL SECURITY;

-- Negocios
ALTER TABLE IF EXISTS negocios ENABLE ROW LEVEL SECURITY;

-- Atividades
ALTER TABLE IF EXISTS atividades ENABLE ROW LEVEL SECURITY;

-- Sync State
ALTER TABLE IF EXISTS sync_state ENABLE ROW LEVEL SECURITY;

-- ============================================
-- POLÍTICAS DE ACESSO - SERVICE ROLE
-- ============================================

DO $$
BEGIN
    -- Pipes
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'pipes') THEN
        DROP POLICY IF EXISTS "Service role full access to pipes" ON pipes;
        CREATE POLICY "Service role full access to pipes" ON pipes FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Agencias
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'agencias') THEN
        DROP POLICY IF EXISTS "Service role full access to agencias" ON agencias;
        CREATE POLICY "Service role full access to agencias" ON agencias FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Corretores
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'corretores') THEN
        DROP POLICY IF EXISTS "Service role full access to corretores" ON corretores;
        CREATE POLICY "Service role full access to corretores" ON corretores FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Usuarios
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'usuarios') THEN
        DROP POLICY IF EXISTS "Service role full access to usuarios" ON usuarios;
        CREATE POLICY "Service role full access to usuarios" ON usuarios FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Proprietarios
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'proprietarios') THEN
        DROP POLICY IF EXISTS "Service role full access to proprietarios" ON proprietarios;
        CREATE POLICY "Service role full access to proprietarios" ON proprietarios FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Clientes
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'clientes') THEN
        DROP POLICY IF EXISTS "Service role full access to clientes" ON clientes;
        CREATE POLICY "Service role full access to clientes" ON clientes FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Imoveis
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'imoveis') THEN
        DROP POLICY IF EXISTS "Service role full access to imoveis" ON imoveis;
        CREATE POLICY "Service role full access to imoveis" ON imoveis FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Negocios
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'negocios') THEN
        DROP POLICY IF EXISTS "Service role full access to negocios" ON negocios;
        CREATE POLICY "Service role full access to negocios" ON negocios FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Atividades
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'atividades') THEN
        DROP POLICY IF EXISTS "Service role full access to atividades" ON atividades;
        CREATE POLICY "Service role full access to atividades" ON atividades FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;

    -- Sync State
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'sync_state') THEN
        DROP POLICY IF EXISTS "Service role full access to sync_state" ON sync_state;
        CREATE POLICY "Service role full access to sync_state" ON sync_state FOR ALL USING (is_service_role()) WITH CHECK (is_service_role());
    END IF;
END $$;

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
