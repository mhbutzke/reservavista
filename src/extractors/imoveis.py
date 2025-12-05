from src.utils.api_client import get_vista_data
from src.utils.supabase_client import update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV
import pandas as pd
import os

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
        update_last_run_in_supabase("imoveis")
        
    return imoveis
