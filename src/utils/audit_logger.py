"""
Sistema de auditoria para rastreamento de operações ETL.
Registra execuções, erros e métricas de performance.
Compliance: LGPD - rastreabilidade de processamento de dados.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import time
from supabase import Client


class AuditLogger:
    """
    Logger de auditoria para operações de ETL.
    Registra todas as operações na tabela audit_logs do Supabase.
    """
    
    def __init__(self, supabase: Client):
        """
        Inicializa o audit logger.
        
        Args:
            supabase: Cliente Supabase autenticado
        """
        self.supabase = supabase
    
    def log_etl_run(
        self,
        entity: str,
        status: str,
        records_processed: int = 0,
        records_failed: int = 0,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None
    ):
        """
        Registra uma execução de ETL.
        
        Args:
            entity: Nome da entidade (clientes, negocios, etc)
            status: Status da operação (SUCCESS, ERROR, WARNING)
            records_processed: Número de registros processados com sucesso
            records_failed: Número de registros que falharam
            errors: Lista de mensagens de erro
            metadata: Metadados adicionais (opcional)
            execution_time_ms: Tempo de execução em milissegundos
        """
        try:
            audit_record = {
                'timestamp': datetime.now().isoformat(),
                'entity': entity,
                'operation': 'ETL_RUN',
                'status': status,
                'records_processed': records_processed,
                'records_failed': records_failed,
                'errors': errors or [],
                'metadata': metadata or {},
                'execution_time_ms': execution_time_ms,
            }
            
            self.supabase.table('audit_logs').insert(audit_record).execute()
            
        except Exception as e:
            # Não queremos que falha no audit quebre o ETL
            print(f"AVISO: Falha ao registrar audit log: {e}")
    
    def log_operation(
        self,
        entity: str,
        operation: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Registra uma operação genérica.
        
        Args:
            entity: Nome da entidade
            operation: Tipo de operação (INSERT, UPDATE, DELETE, etc)
            status: Status da operação
            metadata: Metadados adicionais
        """
        try:
            audit_record = {
                'timestamp': datetime.now().isoformat(),
                'entity': entity,
                'operation': operation,
                'status': status,
                'metadata': metadata or {},
            }
            
            self.supabase.table('audit_logs').insert(audit_record).execute()
            
        except Exception as e:
            print(f"AVISO: Falha ao registrar audit log: {e}")


class ETLTimer:
    """
    Context manager para medir tempo de execução de ETL.
    Integra automaticamente com AuditLogger.
    """
    
    def __init__(self, audit_logger: AuditLogger, entity: str):
        """
        Inicializa o timer.
        
        Args:
            audit_logger: Instance do AuditLogger
            entity: Nome da entidade sendo processada
        """
        self.audit_logger = audit_logger
        self.entity = entity
        self.start_time = None
        self.records_processed = 0
        self.records_failed = 0
        self.errors = []
    
    def __enter__(self):
        """Inicia o timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza o timer e registra audit log."""
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        
        # Determina status baseado em exceção
        if exc_type is not None:
            status = 'ERROR'
            self.errors.append(str(exc_val))
        elif self.records_failed > 0:
            status = 'WARNING'
        else:
            status = 'SUCCESS'
        
        # Registra audit log
        self.audit_logger.log_etl_run(
            entity=self.entity,
            status=status,
            records_processed=self.records_processed,
            records_failed=self.records_failed,
            errors=self.errors if self.errors else None,
            execution_time_ms=execution_time_ms
        )
        
        # Não suprime exceções
        return False
    
    def add_success(self, count: int = 1):
        """Adiciona registros processados com sucesso."""
        self.records_processed += count
    
    def add_failure(self, count: int = 1, error: Optional[str] = None):
        """Adiciona registros que falharam."""
        self.records_failed += count
        if error:
            self.errors.append(error)


# Exemplo de uso:
"""
from src.utils.audit_logger import AuditLogger, ETLTimer
from src.utils.supabase_client import get_supabase_client

supabase = get_supabase_client()
audit = AuditLogger(supabase)

# Uso simples
audit.log_etl_run(
    entity='clientes',
    status='SUCCESS',
    records_processed=150,
    execution_time_ms=2500
)

# Uso com context manager
with ETLTimer(audit, 'clientes') as timer:
    # Processar dados
    for cliente in clientes:
        try:
            save_cliente(cliente)
            timer.add_success()
        except Exception as e:
            timer.add_failure(error=str(e))
"""
