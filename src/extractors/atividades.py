import asyncio
import json
from src.utils.async_api_client import make_async_api_request
from src.config import VISTA_API_KEY

async def fetch_deal_activities(session, deal, fields_atividades):
    deal_id = deal.get("Codigo")
    if not deal_id:
        return []
        
    deal_activities = []
    
    try:
        # Passo 1: Buscar todas as atividades com todos os campos (paginado)
        # A maioria dos negócios tem poucas atividades, então 50 deve cobrir quase tudo.
        # Se precisar de mais, podemos aumentar ou implementar paginação completa aqui.
        params = {
            "key": VISTA_API_KEY,
            "pesquisa": json.dumps({
                "fields": fields_atividades, 
                "paginacao": {"pagina": 1, "quantidade": 50}
            }),
            "codigo_negocio": deal_id
        }
        
        data = await make_async_api_request(session, "negocios/atividades", params=params)
        
        if not data or not isinstance(data, dict):
            return []
            
        # Verificar se temos dados (CodigoAtividade deve estar presente e ser uma lista)
        if "CodigoAtividade" not in data or not isinstance(data["CodigoAtividade"], list):
            return []
            
        num_activities = len(data["CodigoAtividade"])
        if num_activities == 0:
            return []
            
        # Transformar formato colunar em lista de objetos
        # Ex: {"CampoA": [V1, V2], "CampoB": [V1, V2]} -> [{CampoA: V1, CampoB: V1}, {CampoA: V2, CampoB: V2}]
        for i in range(num_activities):
            flat_activity = {"CodigoNegocio": deal_id}
            
            for field in fields_atividades:
                # O campo pode não vir no retorno se estiver vazio para todos, ou pode vir com menos itens (embora raro no Vista)
                # Vamos assumir que as listas estão alinhadas.
                if field in data and isinstance(data[field], list) and len(data[field]) > i:
                    flat_activity[field] = data[field][i]
                else:
                    flat_activity[field] = ""
            
            # Mapear AtividadeCreatedAt para Data
            if "AtividadeCreatedAt" in flat_activity:
                flat_activity["Data"] = flat_activity.pop("AtividadeCreatedAt")
                
            deal_activities.append(flat_activity)
            
        return deal_activities

    except Exception as e:
        print(f"Erro ao extrair atividades do negócio {deal_id}: {e}")
        return []

async def extract_activities(session, deals):
    """
    Extrai atividades de cada negócio usando asyncio.
    """
    print(f"Iniciando extração de atividades para {len(deals)} negócios (Async)...")
    all_activities = []
    
    fields_atividades = [
        "CodigoAtividade", "Assunto", "Texto", "TipoAtividade", "Status", 
        "AtividadeCreatedAt", "ValorProposta", "TextoProposta", 
        "CodigoCliente", "CodigoImovel", "CodigoCorretor", "Automatico"
    ]
    
    # Processar em lotes para não criar milhares de tasks de uma vez
    batch_size = 50
    for i in range(0, len(deals), batch_size):
        batch = deals[i:i + batch_size]
        tasks = [fetch_deal_activities(session, deal, fields_atividades) for deal in batch]
        
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res:
                all_activities.extend(res)
                
        print(f"Processado {min(i + batch_size, len(deals))}/{len(deals)} negócios...")
            
    print(f"Total de atividades extraídas: {len(all_activities)}")
    
    return all_activities

async def enrich_atividades_with_names():
    """
    Executa a função RPC para preencher NomeCorretor e NomeCliente na tabela atividades.
    """
    print("\n--- Enriquecendo Atividades com Nomes (SQL) ---")
    from src.utils.supabase_client import get_supabase_client
    
    supabase = get_supabase_client()
    if not supabase:
        print("Erro: Não foi possível conectar ao Supabase.")
        return

    try:
        response = supabase.rpc('enrich_atividades_names', {}).execute()
        print("Enriquecimento de atividades concluído com sucesso.")
    except Exception as e:
        print(f"Erro ao enriquecer atividades: {e}")
