import os
from datetime import datetime
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY, ENABLE_DATA_VALIDATION, ENABLE_AUDIT_LOGGING
from src.utils.secure_logger import SecureLogger

# Logger seguro
logger = SecureLogger('supabase_client')

def get_supabase_client():
    """Retorna cliente Supabase autenticado."""
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        logger.error("Credenciais do Supabase (URL e KEY) incompletas")
        raise ValueError("SUPABASE_URL e SUPABASE_KEY são obrigatórios")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_last_run_from_supabase(entity_name):
    """
    Recupera a data da última execução para uma entidade específica da tabela 'sync_state' no Supabase.
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        response = supabase.table("sync_state").select("last_run").eq("entity", entity_name).execute()
        
        if response.data and len(response.data) > 0:
            last_run = response.data[0].get("last_run")
            if last_run:
                return last_run.replace("T", " ").split("+")[0].split(".")[0]
            return None
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar last_run para {entity_name}: {e}")
        return None

def update_last_run_in_supabase(entity_name, timestamp=None):
    """
    Atualiza a data da última execução para uma entidade na tabela 'sync_state' no Supabase.
    """
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    supabase = get_supabase_client()
    if not supabase:
        return

    try:
        data = {
            "entity": entity_name,
            "last_run": timestamp,
            "details": {"updated_at": datetime.now().isoformat()}
        }
        supabase.table("sync_state").upsert(data).execute()
        logger.info(f"Sync state atualizado para {entity_name}")
    except Exception as e:
        logger.error(f"Erro ao atualizar sync state para {entity_name}: {e}")

def save_to_supabase(data, table_name, unique_key="Codigo", validator_func=None):
    """
    Salva os dados de uma lista de dicionários em uma tabela do Supabase usando a biblioteca client oficial.
    Realiza UPSERT automaticamente.
    
    Args:
        data: Lista de dicionários com dados
        table_name: Nome da tabela
        unique_key: Chave única para upsert
        validator_func: Função de validação (opcional)
    """
    if not data:
        logger.info(f"Sem dados para salvar na tabela {table_name}")
        return

    supabase = get_supabase_client()
    
    # Validar dados se habilitado e função fornecida
    if ENABLE_DATA_VALIDATION and validator_func:
        from src.utils.validators import validate_batch
        data = validate_batch(data, validator_func)
        logger.info(f"Dados validados: {len(data)} registros válidos")

    # Inicializar audit logger se habilitado
    audit_logger = None
    if ENABLE_AUDIT_LOGGING:
        from src.utils.audit_logger import AuditLogger
        audit_logger = AuditLogger(supabase)
    
    import time
    start_time = time.time()
    records_saved = 0
    records_failed = 0
    
    try:
        logger.info(f"Iniciando UPSERT de {len(data)} registros para {table_name}")
        
        batch_size = 1000
        total_records = len(data)
        
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            
            # Sanitização: Converter strings vazias "" e datas inválidas para None (NULL)
            for item in batch:
                for key, value in item.items():
                    if value == "":
                        item[key] = None
                    elif isinstance(value, str) and (value.startswith("0000-00-00") or value == "0000-00-00 00:00:00"):
                        item[key] = None
            
            try:
                if unique_key:
                    response = supabase.table(table_name).upsert(batch, on_conflict=unique_key).execute()
                else:
                    response = supabase.table(table_name).upsert(batch).execute()
                
                records_saved += len(batch)
                logger.info(f"Lote {i//batch_size + 1} processado ({len(batch)} registros)")
                
            except Exception as batch_err:
                records_failed += len(batch)
                logger.error(f"Erro no lote {i//batch_size + 1}: {batch_err}")

        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Operação concluída para {table_name}: {records_saved} salvos")
        
        # Registrar audit log
        if audit_logger:
            status = 'ERROR' if records_failed > 0 else 'SUCCESS'
            audit_logger.log_etl_run(
                entity=table_name,
                status=status,
                records_processed=records_saved,
                records_failed=records_failed,
                execution_time_ms=execution_time_ms
            )

    except Exception as e:
        logger.error(f"Erro crítico ao salvar em {table_name}: {e}")
        if audit_logger:
            audit_logger.log_etl_run(
                entity=table_name,
                status='ERROR',
                records_failed=total_records,
                errors=[str(e)]
            )
