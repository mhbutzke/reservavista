from src.utils.api_client import get_vista_data
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV
import pandas as pd
import os

def extract_negocios():
    print("\n--- Extraindo Negócios (Deals) ---")
    
    fields_negocios = [
        'Codigo', 'NomePipe', 'UltimaAtualizacao', 'NomeNegocio', 'Status', 
        'DataInicial', 'DataFinal', 'ValorNegocio', 'PrevisaoFechamento', 
        'VeiculoCaptacao', 'CodigoMotivoPerda', 'MotivoPerda', 'ObservacaoPerda', 
        'CodigoPipe', 'EtapaAtual', 'NomeEtapa', 'CodigoCliente', 'NomeCliente', 
        'FotoCliente', 'CodigoImovel', 'StatusAtividades'
    ]
    
    # last_run_time = get_last_run_from_supabase("negocios")
    
    all_negocios = []
    processed_negocios = []
    
    # 1. Listar Pipes (Funis)
    fields_pipes = ["Codigo", "Nome"]
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
                    "Titulo": n.get("NomeNegocio"),
                    "ValorVenda": n.get("ValorNegocio"),
                    "ValorLocacao": None,
                    "Fase": n.get("NomeEtapa"),
                    "DataCadastro": n.get("DataInicial"),
                    "DataAtualizacao": n.get("UltimaAtualizacao"),
                    "DataFechamento": n.get("DataFinal"),
                    "Status": n.get("Status"),
                    "CodigoCliente": n.get("CodigoCliente"),
                    "CodigoCorretor": None,
                    "CodigoAgencia": None,
                    "Origem": n.get("VeiculoCaptacao"),
                    "Midia": None,
                    "Observacao": None,
                    "ObservacaoPerda": n.get("ObservacaoPerda"),
                    "NomeCliente": n.get("NomeCliente"),
                    "NomeCorretor": "",
                    "NomeAgencia": "",
                    "MotivoPerda": n.get("MotivoPerda"),
                    "DataPerda": n.get("DataFinal") if n.get("Status") == "Perdido" else None,
                    "DataGanho": n.get("DataFinal") if n.get("Status") == "Ganho" else None,
                    "PipeID": n.get("CodigoPipe"),
                    "PipeNome": n.get("NomePipe")
                }
                processed_negocios.append(processed_n)
            
        # Salvar Negócios no Supabase
        save_to_supabase(processed_negocios, "negocios", unique_key="Codigo")
        
        # Atualizar last_run se houve sucesso
        if all_negocios:
            update_last_run_in_supabase("negocios")

    else:
        print("Nenhum pipe encontrado. Tentando extração geral de negócios...")

    print(f"\nTotal de negócios extraídos: {len(all_negocios)}")
    
    return all_negocios
