from src.utils.async_api_client import get_vista_data_async
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase

async def extract_clientes(session):
    print("\n--- Extraindo Clientes (Async) ---")
    fields_clientes = [
        "Codigo", "Nome", "CPFCNPJ", "RG", "DataNascimento", "Sexo", "EstadoCivil", "Profissao", "Nacionalidade",
        "EmailResidencial", "FonePrincipal", "Celular", "FoneComercial", "EmailComercial",
        "EnderecoResidencial", "EnderecoNumero", "EnderecoComplemento", "BairroResidencial", "CidadeResidencial", "UFResidencial", "CEPResidencial",
        "Status", "DataCadastro", "Observacoes"
    ]
    
    clientes = await get_vista_data_async(session, "clientes/listar", fields_clientes)
    
    if clientes:
        update_last_run_in_supabase("clientes")
        
    return clientes
