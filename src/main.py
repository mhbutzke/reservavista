import asyncio
import aiohttp
from src.extractors.imoveis import extract_imoveis, enrich_imoveis_with_team
from src.extractors.clientes import extract_clientes
from src.extractors.negocios import extract_negocios, enrich_negocios_with_team
from src.extractors.atividades import extract_activities, enrich_atividades_with_names
from src.extractors.corretores import extract_corretores
from src.extractors.outros import extract_usuarios, extract_agencias, extract_proprietarios, extract_pipes
from src.utils.supabase_client import save_to_supabase, update_last_run_in_supabase
from src.config import SAVE_TO_CSV
import time

async def main():
    start_time = time.time()
    print("--- INICIANDO PROCESSO ETL (ASYNC) ---")

    async with aiohttp.ClientSession() as session:
        # 1. Extrações Independentes (Podem rodar em paralelo)
        # Agrupamos tarefas que não dependem umas das outras
        print(">> Iniciando extrações paralelas (Imóveis, Clientes, Usuários, Agências, Proprietários, Corretores, Pipes)...")
        
        results = await asyncio.gather(
            extract_imoveis(session),
            extract_clientes(session),
            extract_usuarios(session),
            extract_agencias(session),
            extract_proprietarios(session),
            extract_corretores(session),
            extract_pipes(session)
        )
        
        imoveis, clientes, usuarios, agencias, proprietarios, corretores, pipes = results

        # Salvar resultados independentes (Isso pode ser feito enquanto extraímos negócios, mas por simplicidade faremos aqui)
        if imoveis: save_to_supabase(imoveis, "imoveis", unique_key="Codigo")
        if clientes: save_to_supabase(clientes, "clientes", unique_key="Codigo")
        # Usuarios, Agencias, etc já salvam dentro da função (legado) ou podemos refatorar. 
        # Na refatoração atual, mantivemos o save dentro, mas o ideal seria retornar e salvar aqui.
        # Como mantivemos a compatibilidade, eles já salvaram.
        
        # Executar enriquecimento de dados (SQL Updates)
        # Importante: Deve ser feito APÓS salvar imoveis e corretores
        if imoveis or corretores:
            await enrich_imoveis_with_team()

        # 2. Negócios (Deals)
        # Precisamos dos negócios para buscar atividades
        all_negocios = await extract_negocios(session)
        
        if all_negocios:
            # Enriquecer negócios com equipe (SQL)
    try:
        async with aiohttp.ClientSession() as session:
            # 1. Extrações Independentes (Podem rodar em paralelo)
            # Agrupamos tarefas que não dependem umas das outras
            print(">> Iniciando extrações paralelas (Imóveis, Clientes, Usuários, Agências, Proprietários, Corretores, Pipes)...")
            
            results = await asyncio.gather(
                extract_imoveis(session),
                extract_clientes(session),
                extract_usuarios(session),
                extract_agencias(session),
                extract_proprietarios(session),
                extract_corretores(session),
                extract_pipes(session)
            )
            
            imoveis, clientes, usuarios, agencias, proprietarios, corretores, pipes = results

            # Salvar resultados independentes (Isso pode ser feito enquanto extraímos negócios, mas por simplicidade faremos aqui)
            if imoveis: save_to_supabase(imoveis, "imoveis", unique_key="Codigo")
            if clientes: save_to_supabase(clientes, "clientes", unique_key="Codigo")
            # Usuarios, Agencias, etc já salvam dentro da função (legado) ou podemos refatorar. 
            # Na refatoração atual, mantivemos o save dentro, mas o ideal seria retornar e salvar aqui.
            # Como mantivemos a compatibilidade, eles já salvaram.
            
            # Executar enriquecimento de dados (SQL Updates)
            # Importante: Deve ser feito APÓS salvar imoveis e corretores
            if imoveis or corretores:
                await enrich_imoveis_with_team()

            # 2. Negócios (Deals)
            # Precisamos dos negócios para buscar atividades
            all_negocios = await extract_negocios(session)
            
            if all_negocios:
                # Enriquecer negócios com equipe (SQL)
                await enrich_negocios_with_team()
            
            # 3. Atividades (Depende de Negócios)
            if all_negocios:
                print("\n--- Extraindo Atividades (Incremental via Negócios Atualizados) ---")
                atividades = await extract_activities(session, all_negocios)
                if atividades:
                    save_to_supabase(atividades, "atividades", unique_key="CodigoNegocio,CodigoAtividade")
                    # Enriquecer atividades com nomes (SQL)
                    await enrich_atividades_with_names()
            else:
                print("Nenhum negócio novo/atualizado encontrado, pulando extração de atividades.")

    except Exception as e:
        print(f"Erro no loop principal: {e}")

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n--- PROCESSO ETL CONCLUÍDO EM {duration:.2f} SEGUNDOS ---")

if __name__ == "__main__":
    asyncio.run(main())
