from src.extractors.imoveis import extract_imoveis
from src.extractors.clientes import extract_clientes
from src.extractors.negocios import extract_negocios
from src.extractors.atividades import extract_activities
from src.extractors.outros import extract_usuarios, extract_agencias, extract_proprietarios, extract_corretores, extract_pipes
from src.utils.supabase_client import save_to_supabase
from src.config import SAVE_TO_CSV
import pandas as pd
import os

def main():
    print("--- INICIANDO PROCESSO ETL (MODULARIZADO) ---")

    # 1. Imóveis
    imoveis = extract_imoveis()
    if imoveis:
        save_to_supabase(imoveis, "imoveis", unique_key="Codigo")

    # 2. Clientes
    clientes = extract_clientes()
    if clientes:
        save_to_supabase(clientes, "clientes", unique_key="Codigo")

    # 3. Negócios
    all_negocios = extract_negocios()
    
    # 4. Atividades (Depende de Negócios)
    if all_negocios:
        print("\n--- Extraindo Atividades (Incremental via Negócios Atualizados) ---")
        atividades = extract_activities(all_negocios)
        if atividades:
            save_to_supabase(atividades, "atividades", unique_key=None)
    else:
        print("Nenhum negócio novo/atualizado encontrado, pulando extração de atividades.")

    # 5. Outras Entidades
    extract_usuarios()
    extract_agencias()
    extract_proprietarios()
    extract_corretores()
    extract_pipes()

    print("\n--- PROCESSO ETL CONCLUÍDO COM SUCESSO ---")

if __name__ == "__main__":
    main()
