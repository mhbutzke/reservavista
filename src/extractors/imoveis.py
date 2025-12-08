from src.utils.async_api_client import get_vista_data_async
from src.utils.supabase_client import update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV
import pandas as pd
import os

async def extract_imoveis(session):
    print("\n--- Extraindo Imóveis (Async) ---")
    fields_imoveis = [
        "Codigo", "Categoria", "Bairro", "Cidade", "ValorVenda", "ValorLocacao", 
        "AreaTotal", "AreaPrivativa", "Dormitorios", "Suites", "Vagas", "BanheiroSocial",
        "Endereco", "Numero", "Complemento", "CEP", "UF",
        "DataCadastro", "DataAtualizacao", "Status", "Situacao",
        "DescricaoWeb", "TituloSite",
        "CodigoProprietario", "Proprietario", "CodigoCorretor", "CorretorNome", 
        "CodigoAgencia"
    ]
    
    imoveis = await get_vista_data_async(session, "imoveis/listar", fields_imoveis)
    
    if imoveis:
        # Limpar campo CorretorNome (remover prefixo "ID:")
        for imovel in imoveis:
            if "CorretorNome" in imovel and imovel["CorretorNome"] and ":" in imovel["CorretorNome"]:
                parts = imovel["CorretorNome"].split(":", 1)
                if len(parts) > 1:
                    imovel["CorretorNome"] = parts[1].strip()

        update_last_run_in_supabase("imoveis")
        
    return imoveis

async def enrich_imoveis_with_team():
    """
    Executa um comando SQL no Supabase para preencher a equipe do corretor
    cruzando com a tabela de corretores.
    """
    print("\n--- Enriquecendo Imóveis com Equipe (SQL) ---")
    from src.utils.supabase_client import get_supabase_client
    
    supabase = get_supabase_client()
    if not supabase:
        print("Erro: Não foi possível conectar ao Supabase.")
        return

    try:
        # Chamar a função RPC criada no banco
        response = supabase.rpc('enrich_imoveis_team', {}).execute()
        print("Enriquecimento de equipe concluído com sucesso.")
        
    except Exception as e:
        print(f"Erro ao enriquecer imóveis: {e}")
