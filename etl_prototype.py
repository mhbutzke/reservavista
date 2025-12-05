import os
import json
import requests
import pandas as pd
import time
from datetime import datetime
from dotenv import load_dotenv
import concurrent.futures

# Carregar variáveis de ambiente
load_dotenv()

VISTA_API_URL = os.getenv("VISTA_API_URL")
VISTA_API_KEY = os.getenv("VISTA_API_KEY")
SAVE_TO_CSV = os.getenv("SAVE_TO_CSV", "True").lower() == "true"
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "./data")

# Garantir que a URL base tenha o protocolo
if VISTA_API_URL and not VISTA_API_URL.startswith("http"):
    VISTA_API_URL = f"https://{VISTA_API_URL}"

if not os.path.exists(CSV_OUTPUT_DIR):
    os.makedirs(CSV_OUTPUT_DIR)

if not VISTA_API_KEY or not VISTA_API_URL:
    print("ERRO: VISTA_API_KEY e VISTA_API_URL precisam ser definidos no arquivo .env")
    exit(1)

# Configurações Globais
MAX_RETRIES = 5
REQUEST_DELAY = 0.5 # Segundos entre requisições para evitar rate limit
BACKOFF_FACTOR = 1.5 # Fator de multiplicação para o backoff
LAST_RUN_FILE = "last_run.json"

def get_last_run_time(endpoint_name):
    """Lê a data/hora da última execução para um endpoint específico."""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            try:
                data = json.load(f)
                # Retorna a data em formato ISO (YYYY-MM-DD HH:MM:SS) ou None
                return data.get(endpoint_name)
            except json.JSONDecodeError:
                return None
    return None

def update_last_run_time(endpoint_name):
    """Atualiza a data/hora da última execução para o endpoint atual."""
    # Usamos o tempo ATUAL como referência para o PRÓXIMO filtro
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = {}
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {} # Se o arquivo estiver corrompido, resetamos
    
    data[endpoint_name] = now_iso
    
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"[{endpoint_name}] Última execução registrada: {now_iso}")

# --- Funções Auxiliares de Estado (Supabase) ---
def get_last_run_from_supabase(entity_name):
    """
    Recupera a data da última execução para uma entidade específica da tabela 'sync_state' no Supabase.
    Retorna uma string de data (YYYY-MM-DD HH:MM:SS) ou None se não houver registro.
    """
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("Credenciais Supabase ausentes. Retornando None para last_run.")
        return None

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("sync_state").select("last_run").eq("entity", entity_name).execute()
        
        if response.data and len(response.data) > 0:
            last_run = response.data[0].get("last_run")
            # Supabase retorna timestamp com timezone (ISO 8601). O Vista aceita YYYY-MM-DD HH:MM:SS
            # Vamos converter se necessário, ou retornar como está se o formato for compatível.
            # O formato do Vista é 'YYYY-MM-DD HH:MM:SS'. O ISO do Supabase é '2023-10-27T10:00:00+00:00'.
            # Precisamos limpar.
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
    
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        data = {
            "entity": entity_name,
            "last_run": timestamp,
            "details": {"updated_at": datetime.now().isoformat()}
        }
        supabase.table("sync_state").upsert(data).execute()
        print(f"Estado de sincronização atualizado para {entity_name}: {timestamp}")
    except Exception as e:
        print(f"Erro ao atualizar last_run no Supabase para {entity_name}: {e}")

# --- Funções Auxiliares (Legado - Removido) ---
# def load_last_run(): ...
# def save_last_run(): ...


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
                # Implementar outros métodos se necessário
                pass
                
            # Verificar status code
            response.raise_for_status()
            
            # Verificar erro lógico na resposta (API do Vista às vezes retorna 200 com erro no JSON)
            try:
                data = response.json()
                if isinstance(data, dict) and "message" in data and "status" in data and str(data["status"]) != "200":
                    # Se for erro de rate limit ou temporário, podemos tentar novamente?
                    # Geralmente erros lógicos (ex: campo inválido) não adiantam retentar.
                    # Mas vamos logar.
                    print(f"Aviso API (Tentativa {attempt+1}): {data['message']}")
                    # Se for erro fatal, talvez devêssemos parar? Por enquanto retornamos o erro.
                    return data
                return data
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON (Tentativa {attempt+1}): {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição (Tentativa {attempt+1}/{MAX_RETRIES}): {e}")
            if response is not None and response.status_code == 429:
                # Rate limit - esperar mais
                wait_time = (BACKOFF_FACTOR ** attempt) * 2
                print(f"Rate limit atingido. Esperando {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue
            elif response is not None and 500 <= response.status_code < 600:
                # Erro de servidor - tentar novamente
                wait_time = (BACKOFF_FACTOR ** attempt)
                print(f"Erro do servidor. Esperando {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue
            else:
                # Outros erros (400, 404, etc) - não adiantar retentar geralmente
                # Mas para robustez em rede instável, talvez.
                # Por enquanto, vamos assumir que 4xx é erro do cliente e parar.
                if response is not None and 400 <= response.status_code < 500:
                    print("Erro do cliente (4xx). Não haverá retentativa.")
                    return None
        
        # Backoff padrão para outros erros de conexão
        time.sleep(BACKOFF_FACTOR ** attempt)
    
    print(f"Falha após {MAX_RETRIES} tentativas para {endpoint}")
    return None

def get_vista_data(endpoint, fields, primary_date_field=None, filters=None, items_per_page=50, extra_params=None, url_params=None, last_run_time=None):
    """
    Busca dados da API do Vista CRM com paginação automática e filtro incremental.
    `primary_date_field` é o nome do campo de data/hora usado para o filtro (ex: 'DataAtualizacao').
    `last_run_time` é a data da última execução (string) para filtro incremental.
    """
    all_data = []
    page = 1
    has_more = True
    
    print(f"Iniciando extração de {endpoint}...")
    
    # Lógica Incremental
    if primary_date_field and last_run_time:
         # Formato esperado pelo Vista: 'DataAtualizacao >= "2025-12-04 13:00:00"'
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
            
        # Verificar erro lógico retornado pela API (já tratado no make_api_request mas retornado como dict)
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


from supabase import create_client, Client

# --- NOVAS VARIÁVEIS DE AMBIENTE SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def save_to_supabase(data, table_name, unique_key="Codigo"):
    """
    Salva os dados de uma lista de dicionários em uma tabela do Supabase usando a biblioteca client oficial.
    Realiza UPSERT automaticamente.
    """
    if not data:
        print(f"Sem dados para salvar na tabela **{table_name}**.")
        return

    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("ERRO: Credenciais do Supabase (URL e KEY) incompletas no .env")
        return

    try:
        # 1. Inicializar Cliente Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print(f"Iniciando UPSERT de {len(data)} registros para a tabela **{table_name}** via API...")
        
        # 2. Processar dados em lotes (Supabase tem limite de tamanho de payload)
        # Lote seguro: 1000 registros
        batch_size = 1000
        total_records = len(data)
        
        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            
            # Normalizar datas para string ISO (JSON serializable) se necessário
            # O client do supabase geralmente lida bem, mas Pandas Timestamp pode quebrar
            # Se 'data' veio de um to_dict('records') do Pandas, pode ter Timestamps.
            # Se veio direto da API (lista de dicts), está ok (strings).
            # O código atual passa listas de dicts (da API) ou DataFrames convertidos?
            # O código atual passa LISTAS DE DICTS (all_negocios, clientes, etc são listas).
            # Então não precisamos converter Timestamps do Pandas.
            
            # Sanitização: Converter strings vazias "" para None (NULL) para evitar erros em campos numéricos/inteiros
            for item in batch:
                for key, value in item.items():
                    if value == "":
                        item[key] = None
            
            try:
                # Executar UPSERT
                # on_conflict especifica a coluna de unicidade
                response = supabase.table(table_name).upsert(batch, on_conflict=unique_key).execute()

                # Nota: .execute() retorna um objeto response. Se der erro, lança exceção (postgrest-py).
                
                print(f"Lote {i//batch_size + 1} processado ({len(batch)} registros).")
                
            except Exception as batch_err:
                print(f"ERRO no lote {i//batch_size + 1}: {batch_err}")

        print(f"Operação concluída para tabela **{table_name}**.")

    except Exception as e:
        print(f"ERRO CRÍTICO ao conectar/salvar no Supabase para a tabela {table_name}: {e}")

def save_to_csv(data, filename):
    """
    Salva os dados em um arquivo CSV.
    """
    if not data:
        print("Sem dados para salvar.")
        return

    if not os.path.exists(CSV_OUTPUT_DIR):
        os.makedirs(CSV_OUTPUT_DIR)
        
    filepath = os.path.join(CSV_OUTPUT_DIR, filename)
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"Dados salvos em {filepath}")


def extract_clientes():
    print("\n--- Extraindo Clientes ---")
    fields_clientes = [
        "Codigo", "Nome", "CPFCNPJ", "RG", "DataNascimento", "Sexo", "EstadoCivil", "Profissao", "Nacionalidade",
        "EmailResidencial", "FonePrincipal", "Celular", "FoneComercial", "EmailComercial",
        "EnderecoResidencial", "EnderecoNumero", "EnderecoComplemento", "BairroResidencial", "CidadeResidencial", "UFResidencial", "CEPResidencial",
        "Status", "DataCadastro", "Observacoes"
    ]
    
    last_run_time = get_last_run_from_supabase("clientes")
    
    if last_run_time:
        print(f"Sincronização incremental: buscando clientes atualizados após {last_run_time}")
    
    clientes = get_vista_data("clientes/listar", fields_clientes, primary_date_field="DataAtualizacao", last_run_time=last_run_time)
    
    if clientes:
        update_last_run_in_supabase("clientes")
        
    return clientes

def extract_imoveis():
    print("\n--- Extraindo Imóveis ---")
    fields_imoveis = [
        "Codigo", "Categoria", "Bairro", "Cidade", "ValorVenda", "ValorLocacao", 
        "AreaTotal", "AreaPrivativa", "Dormitorios", "Suites", "Vagas", "BanheiroSocial",
        "Endereco", "Numero", "Complemento", "CEP", "UF",
        "DataCadastro", "DataAtualizacao", "Status", "Situacao",
        "DescricaoWeb", "TituloSite"
    ]



    
    
    # Endpoint imoveis/listar não suporta filtro de range (>=), apenas igualdade.
    # Portanto, não é possível fazer sync incremental eficiente via API.
    # Vamos extrair tudo sempre (são ~1200 registros, aceitável).
    
    imoveis = get_vista_data("imoveis/listar", fields_imoveis)
    
    if imoveis:
        # Mesmo extraindo tudo, podemos atualizar o last_run apenas para registro
        update_last_run_in_supabase("imoveis")
        
    return imoveis



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
    
    # Lista validada de campos (removidos Lead e PlacaImovel)
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
            
    print(f"Total de atividades extraídas (antes da deduplicação): {len(all_activities)}")
    
    # Deduplicar por CodigoAtividade
    unique_activities = {act['CodigoAtividade']: act for act in all_activities}.values()
    all_activities = list(unique_activities)
    
    print(f"Total de atividades extraídas (após deduplicação): {len(all_activities)}")
    
    # if should_save:
    #     save_to_csv(all_activities, "atividades.csv")
    
    return all_activities

def extract_usuarios(should_save=True):
    print("\n--- Extraindo Usuários ---")
    fields = [
        "Datacadastro", "RGInscricao", "RGEmissor", "CPFCGC", "Nascimento", "Nacionalidade", 
        "CNH", "CNHExpedicao", "CNHVencimento", "Celular", "Endereco", "Bairro", "Cidade", 
        "UF", "CEP", "Pais", "Fone", "Fax", "E-mail", "Nome", "Observacoes", "Administrativo", 
        "Agenciador", "Gerente", "Empresa", "Codigo", "Celular1", "Celular2", "Corretor", 
        "Datasaida", "Grupoacesso", "Nomecompleto", "Ramal", "Sexo", "Exibirnosite", 
        "RecebeClientesemTrocaautomática", "Inativo", "CRECI", "Estadocivil", 
        "Diretor", "MetadeCaptacoes", "MetaValordeVendas", "EnderecoTipo", "EnderecoNumero", 
        "EnderecoComplemento", "Bloco", "Chat", "CategoriaRanking", "Atuaçãoemvenda", 
        "Atuaçãoemlocação", "DataUltimoLogin", "CodigoAgencia", "Email", "Foto"
    ]
    
    usuarios = get_vista_data("usuarios/listar", fields)
    print(f"Total de usuários extraídos: {len(usuarios)}")
    
    if should_save:
        save_to_csv(usuarios, "usuarios.csv")
    return usuarios

def extract_agencias(should_save=True):
    print("\n--- Extraindo Agências ---")
    fields = [
        "Codigo", "Empresa", "Responsavel", "Endereco", "Bairro", "Cidade", "Cep", "Uf", 
        "Pais", "Fone", "E-mail", "Numero", "Complemento", "CodigoEmpresa", "Nome", "Ddd", 
        "Cnpj", "Cpf", "RazaoSocial", "Fone2", "Celular", "Creci", "Site"
    ]
    
    last_run_time = get_last_run_from_supabase("agencias")
    
    agencias = get_vista_data("agencias/listar", fields, primary_date_field="DataAtualizacao", last_run_time=last_run_time)
    print(f"Total de agências extraídas: {len(agencias)}")
    
    if should_save and agencias:
        save_to_csv(agencias, "agencias.csv")
        
    if agencias:
        update_last_run_in_supabase("agencias")
        
    return agencias

def extract_proprietarios(should_save=True):
    print("\n--- Extraindo Proprietários ---")
    # Removed invalid fields: ContactScore, Relacionamentos, Anexos
    fields = [
        'Codigo', 'FotoCliente', 'Foto', 'CodigoAgencia', 'Corretor', 'Agencia', 'Nome', 
        'CPFCNPJ', 'CreditoSituacao', 'CreditoMensagem', 'CODIGO_CREDPAGO', 'PossuiAnexo', 
        'AnexoCodigoFinalidade'
    ]
    
    last_run_time = get_last_run_from_supabase("proprietarios")
    
    proprietarios = get_vista_data("proprietarios/listar", fields, primary_date_field="DataAtualizacao", last_run_time=last_run_time)
    print(f"Total de proprietários extraídos: {len(proprietarios)}")
    
    if should_save and proprietarios:
        save_to_csv(proprietarios, "proprietarios.csv")
        
    if proprietarios:
        update_last_run_in_supabase("proprietarios")
        
    return proprietarios

def extract_corretores(should_save=True):
    print("\n--- Extraindo Corretores ---")
    # Endpoint retorna poucos campos mesmo com wildcard
    fields = ["Codigo", "Nome"] 
    
    last_run_time = get_last_run_from_supabase("corretores")
    
    corretores = get_vista_data("corretores/listar", fields, primary_date_field="DataAtualizacao", last_run_time=last_run_time)
    print(f"Total de corretores extraídos: {len(corretores)}")
    
    if should_save and corretores:
        save_to_csv(corretores, "corretores.csv")
        
    if corretores:
        update_last_run_in_supabase("corretores")
        
    return corretores


def extract_pipes(should_save=True):
    print("\n--- Extraindo Pipes ---")
    # Requer parametro 'empresa'
    # Vamos pegar o ID da empresa primeiro (hardcoded ou via agencias)
    # Hardcoding 32622 based on debug
    empresa_id = "32622"
    
    fields = ["Codigo", "Nome", "Empresa"]
    
    # Passar empresa como parametro de query (url_params), nao dentro de pesquisa
    pipes = get_vista_data("pipes/listar", fields, url_params={"empresa": empresa_id})
    print(f"Total de pipes extraídos: {len(pipes)}")
    
    if should_save:
        save_to_csv(pipes, "pipes.csv")
    return pipes

def main():
    # 1. Extrair Imóveis (Enriquecido)
    fields_imoveis = [
        "Codigo", "Categoria", "Bairro", "Cidade", "ValorVenda", "ValorLocacao", 
        "AreaTotal", "AreaPrivativa", "Dormitorios", "Suites", "Vagas", "BanheiroSocial",
        "Endereco", "Numero", "Complemento", "CEP", "UF",
        "DataCadastro", "DataAtualizacao", "Status", "Situacao",
        "DescricaoWeb", "TituloSite"
    ]



    # imoveis = get_vista_data("imoveis/listar", fields_imoveis)
    print("--- Extraindo Imóveis ---")
    imoveis = extract_imoveis()
    
    if SAVE_TO_CSV and imoveis:
        save_to_csv(imoveis, "imoveis.csv")
        
    if imoveis:
        save_to_supabase(imoveis, "imoveis", unique_key="Codigo")

    # 1. Extrair Clientes
    print("--- Extraindo Clientes ---")
    clientes = extract_clientes()
    
    # Salvar Clientes no CSV
    if SAVE_TO_CSV:
        save_to_csv(clientes, "clientes")
    
    # Salvar Clientes no Supabase
    save_to_supabase(clientes, "clientes", unique_key="Codigo")






    # Campos para extração de Negócios (Deals) - CORRIGIDO
    fields_negocios = [
        'Codigo', 'NomePipe', 'UltimaAtualizacao', 'NomeNegocio', 'Status', 
        'DataInicial', 'DataFinal', 'ValorNegocio', 'PrevisaoFechamento', 
        'VeiculoCaptacao', 'CodigoMotivoPerda', 'MotivoPerda', 'ObservacaoPerda', 
        'CodigoPipe', 'EtapaAtual', 'NomeEtapa', 'CodigoCliente', 'NomeCliente', 
        'FotoCliente', 'CodigoImovel', 'StatusAtividades', 'CodigoCorretor', 'CodigoAgencia'
    ]
    
    # --- Extração de Negócios ---
    print("\n--- Extraindo Negócios (Deals) ---")
    
    # last_run_data = load_last_run()
    # last_run_time = last_run_data.get("negocios")
    last_run_time = get_last_run_from_supabase("negocios")
    
    all_negocios = []
    processed_negocios = [] # Initialize processed_negocios list
    
    # 1. Listar Pipes (Funis)
    fields_pipes = ["Codigo", "Nome"]
    # Hardcoding empresa_id as it was in extract_pipes
    empresa_id = "32622" 
    pipes = get_vista_data("pipes/listar", fields_pipes, url_params={"empresa": empresa_id})
    
    if pipes:
        print(f"Pipes encontrados: {len(pipes)}")
        for pipe in pipes:
            pipe_id = pipe.get("Codigo")
            pipe_nome = pipe.get("Nome")
            print(f"Extraindo negócios do Pipe: {pipe_nome} (ID: {pipe_id})")
            
            url_params = {"codigo_pipe": pipe_id}
            
            # Endpoint negocios/listar também apresenta problemas com filtro de range (500 Error).
            # Vamos extrair tudo sempre para garantir.
            negocios_pipe = get_vista_data("negocios/listar", fields_negocios, url_params=url_params)
            
            # Processar e mapear os negócios
            for n in negocios_pipe:
                # Adicionar info do pipe (mantido para compatibilidade com all_negocios)
                n["PipeID"] = pipe_id
                n["PipeNome"] = pipe_nome
                all_negocios.append(n) # Adiciona o negócio bruto para a extração de atividades
                
                # Mapeamento para o formato final (Schema SQL)
                processed_n = {
                    "Codigo": n.get("Codigo"),
                    "Titulo": n.get("NomeNegocio"), # Mapeado: NomeNegocio -> Titulo
                    "ValorVenda": n.get("ValorNegocio"), # Mapeado: ValorNegocio -> ValorVenda
                    "ValorLocacao": None, # Não disponível diretamente na lista padrão, assumindo NULL
                    "Fase": n.get("NomeEtapa"), # Mapeado: NomeEtapa -> Fase
                    "DataCadastro": n.get("DataInicial"), # Mapeado: DataInicial -> DataCadastro
                    "DataAtualizacao": n.get("UltimaAtualizacao"), # Mapeado: UltimaAtualizacao -> DataAtualizacao
                    "DataFechamento": n.get("DataFinal"), # Mapeado: DataFinal -> DataFechamento
                    "Status": n.get("Status"),
                    "CodigoCliente": n.get("CodigoCliente"),
                    "CodigoCorretor": n.get("CodigoCorretor"),
                    "CodigoAgencia": n.get("CodigoAgencia"),
                    "Origem": n.get("VeiculoCaptacao"), # Mapeado: VeiculoCaptacao -> Origem
                    "Midia": None,
                    "Observacao": None,
                    "ObservacaoPerda": n.get("ObservacaoPerda"),
                    "NomeCliente": n.get("NomeCliente"),
                    "NomeCorretor": "", # Será preenchido via join no banco se necessário, ou precisa de extração extra
                    "NomeAgencia": "",
                    "MotivoPerda": n.get("MotivoPerda"),
                    "DataPerda": n.get("DataFinal") if n.get("Status") == "Perdido" else None,
                    "DataGanho": n.get("DataFinal") if n.get("Status") == "Ganho" else None,
                    "PipeID": n.get("CodigoPipe"),
                    "PipeNome": n.get("NomePipe")
                }
                processed_negocios.append(processed_n)
            
        # Salvar Negócios no CSV (Backup)
        if SAVE_TO_CSV:
            save_to_csv(processed_negocios, "negocios")
            
        # Salvar Negócios no Supabase
        save_to_supabase(processed_negocios, "negocios", unique_key="Codigo")
        
        # Atualizar last_run se houve sucesso
        if all_negocios:
            # last_run_data["negocios"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # save_last_run(last_run_data)
            update_last_run_in_supabase("negocios")

    else:
        print("Nenhum pipe encontrado. Tentando extração geral de negócios...")
        # Lógica de fallback (opcional) ou erro


    print(f"\nTotal de negócios extraídos: {len(all_negocios)}")
    
    if SAVE_TO_CSV and all_negocios:
        save_to_csv(all_negocios, "negocios.csv")
    
    # Salvar Negócios no Supabase
    save_to_supabase(all_negocios, "negocios", unique_key="Codigo")
        
    # 3. Extrair Atividades (Activities)
    # Se houver negócios novos/atualizados, buscar suas atividades
    if all_negocios:
        print("\n--- Extraindo Atividades (Incremental via Negócios Atualizados) ---")
        # A função extract_activities já itera sobre a lista de negócios fornecida
        # Se all_negocios contém apenas os atualizados, extract_activities buscará apenas atividades desses
        # Precisamos passar a lista de negócios extraídos para buscar atividades relacionadas
        # Como 'all_negocios' contém os dados brutos, podemos usar.
        # Mas 'extract_activities' espera uma lista de IDs ou objetos?
        # Vamos verificar a implementação de extract_activities.
        # Ela itera sobre 'negocios' e pega 'Codigo'.
        
        # Correção do bug: remove 'should_save' argument
        atividades = extract_activities(all_negocios)

        
        # Salvar Atividades no Supabase
        save_to_supabase(atividades, "atividades", unique_key="CodigoAtividade")
    else:
        print("Nenhum negócio novo/atualizado encontrado, pulando extração de atividades.")
        
    # 4. Extrair Outras Entidades (Incremental onde possível)
    
    # 4. Extrair Outras Entidades (Incremental onde possível)
    
    # 4. Extrair Outras Entidades (Incremental onde possível)
    
    # Usuários
    usuarios = extract_usuarios(should_save=SAVE_TO_CSV)
    save_to_supabase(usuarios, "usuarios", unique_key="Codigo")
    
    # Agências
    agencias = extract_agencias(should_save=SAVE_TO_CSV)
    save_to_supabase(agencias, "agencias", unique_key="Codigo")
    
    # Proprietários
    proprietarios = extract_proprietarios(should_save=SAVE_TO_CSV)
    save_to_supabase(proprietarios, "proprietarios", unique_key="Codigo")
    
    # Corretores
    corretores = extract_corretores(should_save=SAVE_TO_CSV)
    save_to_supabase(corretores, "corretores", unique_key="Codigo")

if __name__ == "__main__":
    main()
