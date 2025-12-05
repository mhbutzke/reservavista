from src.utils.api_client import get_vista_data
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase, save_to_supabase
from src.config import SAVE_TO_CSV

def extract_usuarios():
    print("\n--- Extraindo Usuários ---")
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
    
    usuarios = get_vista_data("usuarios/listar", fields)
    print(f"Total de usuários extraídos: {len(usuarios)}")
    
    if usuarios:
        save_to_supabase(usuarios, "usuarios", unique_key="Codigo")
        
    return usuarios

def extract_agencias():
    print("\n--- Extraindo Agências ---")
    fields = [
        "Codigo", "Empresa", "Responsavel", "Endereco", "Bairro", "Cidade", "Cep", "Uf", 
        "Pais", "Fone", "E-mail", "Numero", "Complemento", "CodigoEmpresa", "Nome", "Ddd", 
        "Cnpj", "Cpf", "RazaoSocial", "Fone2", "Celular", "Creci", "Site"
    ]
    
    # last_run_time = get_last_run_from_supabase("agencias")
    
    agencias = get_vista_data("agencias/listar", fields)
    print(f"Total de agências extraídas: {len(agencias)}")
    
    if agencias:
        save_to_supabase(agencias, "agencias", unique_key="Codigo")
        update_last_run_in_supabase("agencias")
        
    return agencias

def extract_proprietarios():
    print("\n--- Extraindo Proprietários ---")
    fields = [
        'Codigo', 'FotoCliente', 'Foto', 'CodigoAgencia', 'Corretor', 'Agencia', 'Nome', 
        'CPFCNPJ', 'CreditoSituacao', 'CreditoMensagem', 'CODIGO_CREDPAGO', 'PossuiAnexo', 
        'AnexoCodigoFinalidade'
    ]
    
    # last_run_time = get_last_run_from_supabase("proprietarios")
    
    proprietarios = get_vista_data("proprietarios/listar", fields)
    print(f"Total de proprietários extraídos: {len(proprietarios)}")
    
    if proprietarios:
        save_to_supabase(proprietarios, "proprietarios", unique_key="Codigo")
        update_last_run_in_supabase("proprietarios")
        
    return proprietarios

def extract_corretores():
    print("\n--- Extraindo Corretores ---")
    fields = ["Codigo", "Nome"] 
    
    # last_run_time = get_last_run_from_supabase("corretores")
    
    corretores = get_vista_data("corretores/listar", fields)
    print(f"Total de corretores extraídos: {len(corretores)}")
    
    if corretores:
        save_to_supabase(corretores, "corretores", unique_key="Codigo")
        update_last_run_in_supabase("corretores")
        
    return corretores

def extract_pipes():
    print("\n--- Extraindo Pipes ---")
    empresa_id = "32622"
    
    fields = ["Codigo", "Nome", "Empresa"]
    
    pipes = get_vista_data("pipes/listar", fields, url_params={"empresa": empresa_id})
    print(f"Total de pipes extraídos: {len(pipes)}")
    
    if pipes:
        save_to_supabase(pipes, "pipes", unique_key="Codigo")
        
    return pipes
