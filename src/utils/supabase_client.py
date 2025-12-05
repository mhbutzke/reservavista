import os
from datetime import datetime
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client():
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("ERRO: Credenciais do Supabase (URL e KEY) incompletas no .env")
        return None
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
        print(f"Erro ao buscar last_run do Supabase para {entity_name}: {e}")
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
        print(f"Estado de sincronização atualizado para {entity_name}: {timestamp}")
    except Exception as e:
        print(f"Erro ao atualizar last_run no Supabase para {entity_name}: {e}")

def save_to_supabase(data, table_name, unique_key="Codigo"):
    """
    Salva os dados de uma lista de dicionários em uma tabela do Supabase usando a biblioteca client oficial.
    Realiza UPSERT automaticamente.
    """
    if not data:
        print(f"Sem dados para salvar na tabela **{table_name}**.")
        return

    supabase = get_supabase_client()
    if not supabase:
        return

    try:
        print(f"Iniciando UPSERT de {len(data)} registros para a tabela **{table_name}** via API...")
        
        batch_size = 1000
        total_records = len(data)
        
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            
            # Sanitização: Converter strings vazias "" para None (NULL)
            for item in batch:
                for key, value in item.items():
                    if value == "":
                        item[key] = None
            
            try:
                if unique_key:
                    response = supabase.table(table_name).upsert(batch, on_conflict=unique_key).execute()
                else:
                    response = supabase.table(table_name).upsert(batch).execute()
                
                print(f"Lote {i//batch_size + 1} processado ({len(batch)} registros).")
                
            except Exception as batch_err:
                print(f"ERRO no lote {i//batch_size + 1}: {batch_err}")

        print(f"Operação concluída para tabela **{table_name}**.")

    except Exception as e:
        print(f"ERRO CRÍTICO ao conectar/salvar no Supabase para a tabela {table_name}: {e}")
