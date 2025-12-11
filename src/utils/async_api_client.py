import aiohttp
import asyncio
import json
from src.config import VISTA_API_URL, VISTA_API_KEY, MAX_RETRIES, BACKOFF_FACTOR, REQUEST_TIMEOUT
from src.utils.secure_logger import SecureLogger

# Logger seguro
logger = SecureLogger('async_api_client')

# Semáforo para limitar concorrência (evitar 429 Rate Limit)
# O Vista CRM pode ser sensível, então começamos conservadores (10)
CONCURRENCY_LIMIT = 10
_semaphore = None

def get_semaphore():
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    return _semaphore

async def make_async_api_request(session, endpoint, params=None, method="GET"):
    """
    Faz uma requisição assíncrona à API com retries, timeouts e backoff.
    """
    url = f"{VISTA_API_URL}/{endpoint}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Configurar timeout
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT, connect=10)
    
    for attempt in range(MAX_RETRIES):
        try:
            async with get_semaphore():  # Respeitar limite de concorrência
                async with session.request(
                    method, url, 
                    params=params, 
                    headers=headers,
                    timeout=timeout
                ) as response:
                        
                    if response.status == 429:
                        wait_time = (BACKOFF_FACTOR ** attempt) * 2
                        logger.warning(f"Rate limit (429) em {endpoint}. Esperando {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    if 500 <= response.status < 600:
                        wait_time = (BACKOFF_FACTOR ** attempt)
                        logger.warning(f"Erro Servidor ({response.status}) em {endpoint}. Esperando {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    response.raise_for_status()
                    
                    try:
                        data = await response.json()
                        # Verificar erro lógico na resposta
                        if isinstance(data, dict) and "status" in data and str(data["status"]) != "200":
                            logger.warning(f"Erro API (Tentativa {attempt+1}): {data.get('message')}")
                            return data 
                        return data
                    except json.JSONDecodeError:
                        text = await response.text()
                        logger.error(f"Erro JSON em {endpoint}: {text[:100]}")
                        return None
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout ({REQUEST_TIMEOUT}s) em {endpoint} (Tentativa {attempt+1}/{MAX_RETRIES})")
            await asyncio.sleep(BACKOFF_FACTOR ** attempt)            
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.warning(f"Recurso não encontrado (404) em {endpoint}. Não será feita nova tentativa.")
                return None
            logger.error(f"Erro HTTP {e.status} ({attempt+1}/{MAX_RETRIES}) em {endpoint}: {e}")
            await asyncio.sleep(BACKOFF_FACTOR ** attempt)
        except aiohttp.ClientError as e:
            logger.error(f"Erro Conexão ({attempt+1}/{MAX_RETRIES}) em {endpoint}: {e}")
            await asyncio.sleep(BACKOFF_FACTOR ** attempt)
            
    logger.error(f"Falha definitiva após {MAX_RETRIES} tentativas para {endpoint}")
    return None

async def get_vista_data_async(session, endpoint, fields, primary_date_field=None, filters=None, items_per_page=50, extra_params=None, url_params=None, last_run_time=None):
    """
    Busca dados da API de forma assíncrona.
    Para paginação, faz a primeira requisição para saber o total de páginas e depois dispara tasks para as demais.
    """
    all_data = []
    
    # 1. Buscar primeira página para obter metadados
    logger.info(f"Iniciando extração async de {endpoint}...")
    
    # Lógica Incremental
    if primary_date_field and last_run_time:
         incremental_filter = {
             primary_date_field: f">= \"{last_run_time}\"" 
         }
         if filters is None:
             filters = incremental_filter
         else:
             filters.update(incremental_filter)

    # Preparar params da primeira página
    params_pesquisa = {
        "fields": fields,
        "paginacao": {
            "pagina": 1,
            "quantidade": items_per_page
        }
    }
    if filters:
        params_pesquisa["filter"] = filters
    if extra_params:
        params_pesquisa.update(extra_params)

    query_params = {
        "key": VISTA_API_KEY,
        "pesquisa": json.dumps(params_pesquisa),
        "showtotal": "1"
    }
    if url_params:
        query_params.update(url_params)

    first_page_data = await make_async_api_request(session, endpoint, params=query_params)
    
    if not first_page_data:
        return []

    # Processar primeira página
    results = []
    if isinstance(first_page_data, dict):
         if "items" in first_page_data and isinstance(first_page_data["items"], list):
             results = first_page_data["items"]
         else:
             for key, value in first_page_data.items():
                 if key not in ['total', 'paginas', 'pagina', 'quantidade', 'meta'] and isinstance(value, dict):
                     results.append(value)
    elif isinstance(first_page_data, list):
        results = first_page_data
        
    all_data.extend(results)
    
    # Calcular total de páginas
    total_pages = 1
    if isinstance(first_page_data, dict):
        if "meta" in first_page_data and isinstance(first_page_data["meta"], dict):
            total_pages = int(first_page_data["meta"].get("totalPages", 1))
        else:
            total_pages = int(first_page_data.get("paginas", 1))
            
    logger.info(f"{endpoint}: Página 1 processada. Total páginas: {total_pages}")
    
    if total_pages <= 1:
        return all_data

    # 2. Disparar requisições para as demais páginas em paralelo
    tasks = []
    for page in range(2, total_pages + 1):
        # Clonar params para não afetar outras iterações
        p_pesquisa = params_pesquisa.copy()
        p_pesquisa["paginacao"] = {"pagina": page, "quantidade": items_per_page}
        
        q_params = query_params.copy()
        q_params["pesquisa"] = json.dumps(p_pesquisa)
        
        # Corretores usa paginação na URL
        if "meta" in first_page_data: 
             q_params["page"] = page

        tasks.append(make_async_api_request(session, endpoint, params=q_params))
        
    # Aguardar todas as páginas
    pages_results = await asyncio.gather(*tasks)
    
    for i, page_data in enumerate(pages_results):
        if not page_data:
            continue
            
        p_results = []
        if isinstance(page_data, dict):
             if "items" in page_data and isinstance(page_data["items"], list):
                 p_results = page_data["items"]
             else:
                 for key, value in page_data.items():
                     if key not in ['total', 'paginas', 'pagina', 'quantidade', 'meta'] and isinstance(value, dict):
                         p_results.append(value)
        elif isinstance(page_data, list):
            p_results = page_data
            
        all_data.extend(p_results)
        
    logger.info(f"{endpoint}: Extração concluída. Total registros: {len(all_data)}")
    return all_data
