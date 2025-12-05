import concurrent.futures
import json
from src.utils.api_client import make_api_request
from src.config import VISTA_API_KEY

def fetch_deal_activities(deal, fields_atividades):
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
        
        # Usar make_api_request para buscar IDs
        data = make_api_request("negocios/atividades", params=params)
        
        if not data:
            return []
            
        activity_ids = data.get("CodigoAtividade", [])
        
        if not activity_ids:
            return []
            
        # Passo 2: Buscar detalhes de cada atividade individualmente
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
            
            # Usar make_api_request para buscar detalhes
            detail_data = make_api_request("negocios/atividades", params=params_detail)
            
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

def extract_activities(deals):
    """
    Extrai atividades de cada negócio usando paralelismo e estratégia de busca por ID.
    """
    print(f"Iniciando extração de atividades para {len(deals)} negócios (Paralelo - Estratégia ID)...")
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
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_deal = {executor.submit(fetch_deal_activities, deal, fields_atividades): deal for deal in deals}
        
        count = 0
        total = len(deals)
        
        for future in concurrent.futures.as_completed(future_to_deal):
            count += 1
            if count % 50 == 0:
                print(f"Processado {count}/{total} negócios...")
            
            try:
                data = future.result()
                if data:
                    all_activities.extend(data)
            except Exception as e:
                print(f"Erro na thread: {e}")
            
    print(f"Total de atividades extraídas: {len(all_activities)}")
    
    return all_activities
