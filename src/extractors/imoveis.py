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
        "DescricaoWeb", "TituloSite"
    ]
    
    imoveis = await get_vista_data_async(session, "imoveis/listar", fields_imoveis)
    
    if imoveis:
        update_last_run_in_supabase("imoveis")
        
    return imoveis
