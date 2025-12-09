from src.utils.async_api_client import get_vista_data_async, make_async_api_request
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV, VISTA_API_KEY
import pandas as pd
import os
import asyncio
import json

async def fetch_deal_details(session, deal_id):
    """
    Busca detalhes de um negócio específico para obter dados do corretor.
    """
    try:
        params = {
            "key": VISTA_API_KEY,
            "codigo_negocio": deal_id
        }
        data = await make_async_api_request(session, "negocios/detalhes", params=params)
        return data
    except Exception as e:
        print(f"Erro ao buscar detalhes do negócio {deal_id}: {e}")
        return None

async def enrich_deals_with_details(session, deals):
    """
    Enriquece a lista de negócios com detalhes (corretor) em paralelo.
    """
    print(f"Enriquecendo {len(deals)} negócios com detalhes...")
    enriched_deals = []
    
    # Processar em lotes
    batch_size = 50
    for i in range(0, len(deals), batch_size):
        batch = deals[i:i + batch_size]
        tasks = [fetch_deal_details(session, d.get("Codigo")) for d in batch]
        
        results = await asyncio.gather(*tasks)
        
        for original_deal, details in zip(batch, results):
            if details:
                # Mesclar detalhes no dicionário original
                # Prioridade para o original, mas adicionamos o que falta (CorretoresNegocio)
                original_deal.update(details)
            enriched_deals.append(original_deal)
            
        print(f"Enriquecido {min(i + batch_size, len(deals))}/{len(deals)} negócios...")
        
    return enriched_deals

async def extract_negocios(session):
    print("\n--- Extraindo Negócios (Deals) - Async ---")
    
    fields_negocios = [
        'Codigo', 'NomePipe', 'UltimaAtualizacao', 'NomeNegocio', 'Status', 
        'DataInicial', 'DataFinal', 'ValorNegocio', 'PrevisaoFechamento', 
        'VeiculoCaptacao', 'CodigoMotivoPerda', 'MotivoPerda', 'ObservacaoPerda', 
        'CodigoPipe', 'EtapaAtual', 'NomeEtapa', 'CodigoCliente', 'NomeCliente', 
        'FotoCliente', 'CodigoImovel', 'StatusAtividades'
    ]
    
    all_negocios = []
    processed_negocios = []
    
    # 1. Listar Pipes (Funis)
    fields_pipes = ["Codigo", "Nome"]
    empresa_id = "32622" 
    pipes = await get_vista_data_async(session, "pipes/listar", fields_pipes, url_params={"empresa": empresa_id})
    
    if pipes:
        print(f"Pipes encontrados: {len(pipes)}")
        for pipe in pipes:
            pipe_id = pipe.get("Codigo")
            pipe_nome = pipe.get("Nome")
            print(f"Extraindo negócios do Pipe: {pipe_nome} (ID: {pipe_id})")
            
            url_params = {"codigo_pipe": pipe_id}
            
            # Endpoint negocios/listar também apresenta problemas com filtro de range (500 Error).
            # Vamos extrair tudo sempre para garantir.
            negocios_pipe = await get_vista_data_async(session, "negocios/listar", fields_negocios, url_params=url_params)
            
            if negocios_pipe:
                # Enriquecer com detalhes (Corretor)
                negocios_pipe = await enrich_deals_with_details(session, negocios_pipe)

            # Processar e mapear os negócios
            for n in negocios_pipe:
                # Adicionar info do pipe (mantido para compatibilidade com all_negocios)
                n["PipeID"] = pipe_id
                n["PipeNome"] = pipe_nome
                all_negocios.append(n) # Adiciona o negócio bruto para a extração de atividades
                
                # Extrair dados do corretor (pode haver múltiplos, pegamos o primeiro por enquanto)
                codigo_corretor = None
                nome_corretor = ""
                
                corretores = n.get("CorretoresNegocio")
                if corretores and isinstance(corretores, list) and len(corretores) > 0:
                    first_broker = corretores[0]
                    codigo_corretor = first_broker.get("CorretorNegocio")
                    nome_corretor = first_broker.get("NomeCorretor")

                # Mapeamento para o formato final (Schema SQL)
                # Mapeamento para o formato final (Schema SQL)
                processed_n = {
                    "Codigo": n.get("Codigo"),
                    "NomeNegocio": n.get("NomeNegocio"),
                    "ValorNegocio": n.get("ValorNegocio"),
                    "ValorLocacao": None,
                    "NomeEtapa": n.get("NomeEtapa"),
                    "EtapaAtual": n.get("EtapaAtual"),
                    "DataInicial": n.get("DataInicial"),
                    "UltimaAtualizacao": n.get("UltimaAtualizacao"),
                    "DataFinal": n.get("DataFinal"),
                    "PrevisaoFechamento": n.get("PrevisaoFechamento"),
                    "Status": n.get("Status"),
                    "CodigoCliente": n.get("CodigoCliente"),
                    "FotoCliente": n.get("FotoCliente"),
                    "CodigoCorretor": codigo_corretor,
                    "VeiculoCaptacao": n.get("VeiculoCaptacao"),
                    "CodigoImovel": n.get("CodigoImovel"),
                    "ObservacaoPerda": n.get("ObservacaoPerda"),
                    "NomeCliente": n.get("NomeCliente"),
                    "NomeCorretor": nome_corretor.split(":")[1].strip() if nome_corretor and ":" in nome_corretor else nome_corretor,
                    "MotivoPerda": n.get("MotivoPerda"),
                    "CodigoMotivoPerda": n.get("CodigoMotivoPerda"),
                    "DataPerda": n.get("DataFinal") if n.get("Status") == "Perdido" else None,
                    "DataGanho": n.get("DataFinal") if n.get("Status") == "Ganho" else None,
                    "CodigoPipe": n.get("CodigoPipe"),
                    "NomePipe": n.get("NomePipe"),
                    "StatusAtividades": n.get("StatusAtividades"),
                    "EquipeCorretor": None # Será preenchido via SQL enrichment
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

async def enrich_negocios_with_team():
    """
    Executa um comando SQL no Supabase para preencher a equipe do corretor
    cruzando com a tabela de corretores.
    """
    print("\n--- Enriquecendo Negócios com Equipe (SQL) ---")
    from src.utils.supabase_client import get_supabase_client
    
    supabase = get_supabase_client()
    if not supabase:
        print("Erro: Não foi possível conectar ao Supabase.")
        return

    try:
        # Chamar a função RPC criada no banco
        response = supabase.rpc('enrich_negocios_team', {}).execute()
        print("Enriquecimento de equipe de negócios concluído com sucesso.")
        
    except Exception as e:
        print(f"Erro ao enriquecer negócios: {e}")
