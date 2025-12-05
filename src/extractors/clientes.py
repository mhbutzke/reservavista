from src.utils.api_client import get_vista_data
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase

def extract_clientes():
    print("\n--- Extraindo Clientes ---")
    fields_clientes = [
        "Codigo", "Nome", "CPFCNPJ", "RG", "DataNascimento", "Sexo", "EstadoCivil", "Profissao", "Nacionalidade",
        "EmailResidencial", "FonePrincipal", "Celular", "FoneComercial", "EmailComercial",
        "EnderecoResidencial", "EnderecoNumero", "EnderecoComplemento", "BairroResidencial", "CidadeResidencial", "UFResidencial", "CEPResidencial",
        "Status", "DataCadastro", "Observacoes"
    ]
    
    # Incremental sync disabled due to API issues with date filtering
    # last_run_time = get_last_run_from_supabase("clientes")
    # if last_run_time:
    #     print(f"Sincronização incremental: buscando clientes atualizados após {last_run_time}")
    
    clientes = get_vista_data("clientes/listar", fields_clientes)
    
    if clientes:
        update_last_run_in_supabase("clientes")
        
    return clientes
