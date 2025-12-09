from src.utils.async_api_client import get_vista_data_async
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV

async def extract_usuarios(session):
    print("\n--- Extraindo Usuários (Async) ---")
    fields = [
        "Datacadastro", "RGInscricao", "RGEmissor", "CPFCGC", "Nascimento", "Nacionalidade", 
        "CNH", "CNHExpedicao", "CNHVencimento", "Celular", "Endereco", "Bairro", "Cidade", 
        "UF", "CEP", "Pais", "Fone", "Fax", "E-mail", "Nome", "Observacoes", "Administrativo", 
        "Agenciador", "Gerente", "Empresa", "Codigo", "Celular1", "Celular2", "Corretor", 
        "Datasaida", "Grupoacesso", "Nomecompleto", "Ramal", "Sexo", "Exibirnosite", 
        "RecebeClientesemTrocaautomática", "Inativo", "CRECI", "Estadocivil", 
        "Diretor", "MetadeCaptacoes", "MetaValordeVendas", "EnderecoTipo", "EnderecoNumero", 
        "EnderecoComplemento", "Bloco", "Chat", "CategoriaRanking", "Atuaçãoemvenda", 
        "Atuaçãoemlocação", "DataUltimoLogin", "CodigoAgencia", "Email", "Foto"
    ]
    
    usuarios = await get_vista_data_async(session, "usuarios/listar", fields)
    print(f"Total de usuários extraídos: {len(usuarios)}")
    
    if usuarios:
        save_to_supabase(usuarios, "usuarios", unique_key="Codigo")
        
    return usuarios

async def extract_agencias(session):
    print("\n--- Extraindo Agências (Async) ---")
    fields = [
        "Codigo", "Empresa", "Responsavel", "Endereco", "Bairro", "Cidade", "Cep", "Uf", 
        "Pais", "Fone", "E-mail", "Numero", "Complemento", "CodigoEmpresa", "Nome", "Ddd", 
        "Cnpj", "Cpf", "RazaoSocial", "Fone2", "Celular", "Creci", "Site"
    ]
    
    agencias = await get_vista_data_async(session, "agencias/listar", fields)
    print(f"Total de agências extraídas: {len(agencias)}")
    
    if agencias:
        save_to_supabase(agencias, "agencias", unique_key="Codigo")
        update_last_run_in_supabase("agencias")
        
    return agencias

async def extract_proprietarios(session):
    print("\n--- Extraindo Proprietários (Async) ---")
    fields = [
        'Codigo', 'FotoCliente', 'Foto', 'CodigoAgencia', 'Corretor', 'Agencia', 'Nome', 
        'CPFCNPJ', 'CreditoSituacao', 'CreditoMensagem', 'CODIGO_CREDPAGO', 'PossuiAnexo', 
        'AnexoCodigoFinalidade'
    ]
    
    proprietarios = await get_vista_data_async(session, "proprietarios/listar", fields)
    print(f"Total de proprietários extraídos: {len(proprietarios)}")
    
    if proprietarios:
        save_to_supabase(proprietarios, "proprietarios", unique_key="Codigo")
        update_last_run_in_supabase("proprietarios")
        
    return proprietarios



async def extract_pipes(session):
    print("\n--- Extraindo Pipes (Async) ---")
    empresa_id = "32622"
    
    fields = ["Codigo", "Nome", "Empresa"]
    
    pipes = await get_vista_data_async(session, "pipes/listar", fields, url_params={"empresa": empresa_id})
    print(f"Total de pipes extraídos: {len(pipes)}")
    
    if pipes:
        save_to_supabase(pipes, "pipes", unique_key="Codigo")
        
    return pipes
