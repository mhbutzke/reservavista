-- Migration: Audit Logs Table (SIMPLIFIED VERSION - No Encryption)
-- Descrição: Versão simplificada focada apenas em audit logs
-- Data: 2025-12-10
-- NOTA: Criptografia de CPF removida conforme feedback do usuário

-- ============================================
-- TABELA DE AUDIT LOGS
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entity TEXT NOT NULL,
    operation TEXT NOT NULL, -- INSERT, UPDATE, DELETE, ETL_RUN
    status TEXT NOT NULL, -- SUCCESS, ERROR, WARNING
    records_processed INTEGER,
    records_failed INTEGER,
    errors JSONB,
    metadata JSONB,
    execution_time_ms INTEGER,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- ÍNDICES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
  ON audit_logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_entity 
  ON audit_logs(entity);

CREATE INDEX IF NOT EXISTS idx_audit_status 
  ON audit_logs(status);

CREATE INDEX IF NOT EXISTS idx_audit_operation 
  ON audit_logs(operation);

CREATE INDEX IF NOT EXISTS idx_audit_date_range 
  ON audit_logs(timestamp, entity);

-- ============================================
-- RLS PARA AUDIT LOGS
-- ============================================

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Apenas service role pode ler/escrever
CREATE POLICY "Service role full access to audit_logs"
  ON audit_logs
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- ============================================
-- FUNÇÃO PARA LIMPAR LOGS ANTIGOS
-- ============================================

CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM audit_logs
  WHERE timestamp < NOW() - (days_to_keep || ' days')::INTERVAL;
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  RAISE NOTICE 'Deleted % old audit log records', deleted_count;
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- VIEW PARA ESTATÍSTICAS
-- ============================================

CREATE OR REPLACE VIEW audit_stats AS
SELECT 
  entity,
  operation,
  status,
  COUNT(*) as total_operations,
  SUM(records_processed) as total_records,
  AVG(execution_time_ms) as avg_execution_time_ms,
  MAX(execution_time_ms) as max_execution_time_ms,
  DATE_TRUNC('day', timestamp) as date
FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY entity, operation, status, DATE_TRUNC('day', timestamp)
ORDER BY date DESC, entity;

-- ============================================
-- FUNÇÃO PARA OBTER ÚLTIMAS EXECUÇÕES
-- ============================================

CREATE OR REPLACE FUNCTION get_recent_etl_runs(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
  entity TEXT,
  timestamp TIMESTAMPTZ,
  status TEXT,
  records_processed INTEGER,
  execution_time_ms INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    a.entity,
    a.timestamp,
    a.status,
    a.records_processed,
    a.execution_time_ms
  FROM audit_logs a
  WHERE a.operation = 'ETL_RUN'
  ORDER BY a.timestamp DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- COMENTÁRIOS
-- ============================================

COMMENT ON TABLE audit_logs IS 'Registros de auditoria para rastreamento de operações - Uso interno';
COMMENT ON FUNCTION cleanup_old_audit_logs(INTEGER) IS 'Remove logs antigos - executar mensalmente';
COMMENT ON VIEW audit_stats IS 'Estatísticas agregadas de auditoria dos últimos 30 dias';

-- ============================================
-- VERIFICAÇÃO
-- ============================================

-- Para testar:
-- SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;
-- SELECT * FROM audit_stats LIMIT 10;
-- SELECT * FROM get_recent_etl_runs(5);
