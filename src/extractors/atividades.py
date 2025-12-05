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
        # Passo 1: Buscar lista de IDs de atividades (Facets)
        params = {
            "key": VISTA_API_KEY,
            "pesquisa": json.dumps({"fields": ["CodigoAtividade"], "paginacao": {"pagina": 1, "quantidade": 50}}),
            "codigo_negocio": deal_id
        }
        
        # Usar make_async_api_request para buscar IDs
        data = await make_async_api_request(session, "negocios/atividades", params=params)
        
        if not data:
            return []
            
        activity_ids = data.get("CodigoAtividade", [])
        
        if not activity_ids:
            return []
            
        # Passo 2: Buscar detalhes de cada atividade individualmente (em paralelo)
        tasks = []
        for act_id in activity_ids:
            # Filtrar por ID específico para obter o registro completo
            params_detail = {
                "key": VISTA_API_KEY,
                "pesquisa": json.dumps({
                    "fields": fields_atividades, 
                    "paginacao": {"pagina": 1, "quantidade": 1},
                    "filter": {"CodigoAtividade": act_id}
                }),
                "codigo_negocio": deal_id
            }
            tasks.append(make_async_api_request(session, "negocios/atividades", params=params_detail))
            
        details_results = await asyncio.gather(*tasks)
        
        for detail_data in details_results:
            if detail_data:
                # O retorno é {"Campo": ["Valor"], ...}
                # Precisamos "flatten" isso para um objeto simples
                flat_activity = {"CodigoNegocio": deal_id}
                for k, v in detail_data.items():
                    if isinstance(v, list) and len(v) > 0:
                        flat_activity[k] = v[0]
                    else:
                        flat_activity[k] = v
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
        "CodigoImovel", "ValorProposta", "EstadoProposta", "TextoProposta", "Aceitacao", "Automatico", 
        "Numero", "Texto", "Pendente", "Assunto", "EtapaAcaoId", "EtapaAcao", "TipoAtividade", 
        "TipoAtividadeId", "MotivoLost", "CodigoEmImovel", "Hora", "AtividadeCreatedAt", 
        "AtividadeUpdatedAt", "Data", "CodigoCliente", "CodigoAtividade", "CodigoCorretor", 
        "NumeroAgenda", "DataHora", "DataAtualizacao", "Local", "Inicio", "Final", "Prioridade", 
        "Privado", "AlertaMinutos", "Excluido", "Concluido", "Tarefa", "DataConclusao", "DiaInteiro", 
        "TipoAgenda", "CodigoDev", "IdGoogleCalendar", "StatusVisita", "CodigoImobiliaria", 
        "Icone", "Duracao", "FotoCorretor", "Status"
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
