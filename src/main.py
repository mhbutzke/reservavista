import asyncio
import aiohttp
from src.extractors.imoveis import extract_imoveis
from src.extractors.clientes import extract_clientes
from src.extractors.negocios import extract_negocios
from src.extractors.atividades import extract_activities
from src.extractors.outros import extract_usuarios, extract_agencias, extract_proprietarios, extract_corretores, extract_pipes
from src.utils.supabase_client import save_to_supabase
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

        # 2. Negócios (Deals)
        # Precisamos dos negócios para buscar atividades
        all_negocios = await extract_negocios(session)
        
        # 3. Atividades (Depende de Negócios)
        if all_negocios:
            print("\n--- Extraindo Atividades (Incremental via Negócios Atualizados) ---")
            atividades = await extract_activities(session, all_negocios)
            if atividades:
                save_to_supabase(atividades, "atividades", unique_key=None)
        else:
            print("Nenhum negócio novo/atualizado encontrado, pulando extração de atividades.")

    end_time = time.time()
    duration = end_time - start_time
    print(f"\n--- PROCESSO ETL CONCLUÍDO EM {duration:.2f} SEGUNDOS ---")

if __name__ == "__main__":
    asyncio.run(main())
