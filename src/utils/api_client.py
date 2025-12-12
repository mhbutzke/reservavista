import requests
import time
import json
from src.config import VISTA_API_URL, VISTA_API_KEY, MAX_RETRIES, REQUEST_DELAY, BACKOFF_FACTOR

def make_api_request(endpoint, params=None, method="GET"):
    """
    Função auxiliar para fazer requisições à API com tratamento de erros e retries.
    """
    url = f"{VISTA_API_URL}/{endpoint}"
    headers = {"Accept": "application/json"}
    
    # Adicionar delay preventivo
    time.sleep(REQUEST_DELAY)
    
    for attempt in range(MAX_RETRIES):
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers)
            else:
                # Passar outros métodos para requests.request
                response = requests.request(method, url, params=params, headers=headers, json=params if method in ['POST', 'PUT', 'PATCH'] else None)
                
            # Verificar status code
            response.raise_for_status()
            
            # Verificar erro lógico na resposta (API do Vista às vezes retorna 200 com erro no JSON)
            try:
                data = response.json()
                if isinstance(data, dict) and "message" in data and "status" in data and str(data["status"]) != "200":
                    print(f"Aviso API (Tentativa {attempt+1}): {data['message']}")
                    return data
                return data
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON (Tentativa {attempt+1}): {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição (Tentativa {attempt+1}/{MAX_RETRIES}): {e}")
            if 'response' in locals() and response is not None:
                if response.status_code == 429:
                    wait_time = (BACKOFF_FACTOR ** attempt) * 2
                    print(f"Rate limit atingido. Esperando {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                elif 500 <= response.status_code < 600:
                    wait_time = (BACKOFF_FACTOR ** attempt)
                    print(f"Erro do servidor. Esperando {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    continue
                elif 400 <= response.status_code < 500:
                    print("Erro do cliente (4xx). Não haverá nova tentativa.")
                    return None
        
        # Backoff padrão para outros erros de conexão
        time.sleep(BACKOFF_FACTOR ** attempt)
    
    print(f"Falha após {MAX_RETRIES} tentativas para {endpoint}")
    return None

def get_vista_data(endpoint, fields, primary_date_field=None, filters=None, items_per_page=50, extra_params=None, url_params=None, last_run_time=None):
    """
    Busca dados da API do Vista CRM com paginação automática e filtro incremental.
    """
    all_data = []
    page = 1
    has_more = True
    
    print(f"Iniciando extração de {endpoint}...")
    
    # Lógica Incremental
    if primary_date_field and last_run_time:
         incremental_filter = {
             primary_date_field: f">= \"{last_run_time}\"" 
         }
         print(f"Filtro Incremental: {primary_date_field} a partir de {last_run_time}")
         
         if filters is None:
             filters = incremental_filter
         else:
             filters.update(incremental_filter)
    elif primary_date_field:
         print("Primeira execução ou registro não encontrado. Fazendo extração COMPLETA.")

    use_url_pagination = False
    
    while has_more:
        print(f"Buscando página {page}...")
        
        # Montar parâmetros da requisição (JSON 'pesquisa')
        params_pesquisa = {
            "fields": fields,
            "paginacao": {
                "pagina": page,
                "quantidade": items_per_page
            }
        }
        
        if filters:
            params_pesquisa["filter"] = filters
            
        if extra_params:
            params_pesquisa.update(extra_params)

        # Parâmetros da URL
        query_params = {
            "key": VISTA_API_KEY,
            "pesquisa": json.dumps(params_pesquisa),
            "showtotal": "1"
        }
        
        if use_url_pagination:
            query_params["page"] = page
        
        if url_params:
            query_params.update(url_params)
        
        # Fazer requisição usando a função auxiliar
        data = make_api_request(endpoint, params=query_params)
        
        if not data:
            print("Falha ao obter dados ou dados vazios.")
            break
            
        # Verificar erro lógico retornado pela API
        if isinstance(data, dict) and "status" in data and str(data["status"]) != "200":
             print(f"Erro na API: {data.get('message')}")
             break

        # Normalizar resultados
        results = []
        if isinstance(data, dict):
             if "items" in data and isinstance(data["items"], list):
                 results = data["items"]
             else:
                 for key, value in data.items():
                     if key not in ['total', 'paginas', 'pagina', 'quantidade', 'meta'] and isinstance(value, dict):
                         results.append(value)
        elif isinstance(data, list):
            results = data
        
        if not results:
            print("Nenhum dado encontrado nesta página.")
            has_more = False
            break
            
        all_data.extend(results)
        
        # Verificar paginação
        total_records = 0
        total_pages = 1
        
        if "meta" in data and isinstance(data["meta"], dict):
            # Estrutura do endpoint corretores
            total_records = int(data["meta"].get("totalItems", 0))
            total_pages = int(data["meta"].get("totalPages", 1))
            use_url_pagination = True
        else:
            # Estrutura padrão
            total_records = int(data.get("total", 0))
            total_pages = int(data.get("paginas", 1))
        
        print(f"Página {page} processada. {len(results)} registros obtidos. (Total páginas: {total_pages})")
        
        if page >= total_pages:
            has_more = False
        else:
            page += 1
            
    print(f"Extração concluída. Total de {len(all_data)} registros.")
    
    return all_data
