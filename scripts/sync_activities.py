import asyncio
import sys
import os
import aiohttp
from dotenv import load_dotenv

# Add parent directory to path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.supabase_client import get_supabase_client, save_to_supabase
from src.extractors.atividades import extract_activities, enrich_atividades_with_names

async def run_activities_sync():
    load_dotenv()
    
    supabase = get_supabase_client()
    if not supabase:
        print("Erro ao conectar ao Supabase")
        return
    
    print("--- Iniciando Sincronização de Atividades (Agendada) ---")
    
    # 1. Buscar todos os negócios do Supabase (para ter os IDs)
    print("Buscando todos os IDs de negócios no Supabase...")
    all_deals = []
    offset = 0
    chunk_size = 1000
    while True:
        res = supabase.table("negocios").select("Codigo,CodigoCliente,NomeCliente,CodigoCorretor,NomeCorretor").range(offset, offset + chunk_size - 1).execute()
        if not res.data:
            break
        all_deals.extend(res.data)
        print(f"Carregados {len(all_deals)} negócios...")
        offset += chunk_size
        
    print(f"Total de negócios para processar: {len(all_deals)}")
    
    # 2. Extrair atividades da API Vista
    async with aiohttp.ClientSession() as session:
        activities = await extract_activities(session, all_deals)
        
        # 3. Salvar no Supabase
        if activities:
            print(f"Salvando {len(activities)} atividades no Supabase...")
            save_to_supabase(activities, "atividades", unique_key="CodigoNegocio,CodigoAtividade")
            
            # 4. Enriquecer com nomes (SQL)
            await enrich_atividades_with_names()
        else:
            print("Nenhuma atividade encontrada.")

if __name__ == "__main__":
    asyncio.run(run_activities_sync())
