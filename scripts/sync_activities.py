import asyncio
import sys
import os
import aiohttp
from dotenv import load_dotenv

# Add parent directory to path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.supabase_client import get_supabase_client, save_to_supabase
from src.extractors.atividades import extract_activities, enrich_atividades_with_names
from src.extractors.negocios import extract_negocios, enrich_negocios_with_team

async def run_activities_sync():
    load_dotenv()
    
    supabase = get_supabase_client()
    if not supabase:
        print("Erro ao conectar ao Supabase")
        return
    
    print("--- Iniciando Sincronização de Negócios e Atividades (Agendada) ---")
    
    async with aiohttp.ClientSession() as session:
        # 1. Extrair e Salvar Negócios (Deals) da API Vista
        # Isso garante que temos os negócios mais recentes antes de buscar atividades
        print(">>> Etapa 1: Atualizando Negócios...")
        all_deals = await extract_negocios(session)
        
        if all_deals:
            # Enriquecer negócios com equipe (SQL)
            await enrich_negocios_with_team()
            
            # 2. Extrair atividades para esses negócios
            print(f"\n>>> Etapa 2: Atualizando Atividades para {len(all_deals)} negócios...")
            activities = await extract_activities(session, all_deals)
            
            # 3. Salvar Atividades no Supabase
            if activities:
                print(f"Salvando {len(activities)} atividades no Supabase...")
                save_to_supabase(activities, "atividades", unique_key="CodigoNegocio,CodigoAtividade")
                
                # 4. Enriquecer com nomes (SQL)
                await enrich_atividades_with_names()
            else:
                print("Nenhuma atividade encontrada.")
        else:
            print("Nenhum negócio encontrado na extração.")

if __name__ == "__main__":
    asyncio.run(run_activities_sync())
