import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_connection():
    print("Testando conexão com Supabase (REST API)...")
    
    if not all([SUPABASE_URL, SUPABASE_KEY]):
        print("ERRO: Credenciais incompletas.")
        return

    try:
        # 1. Inicializar Cliente
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Cliente Supabase inicializado.")
        
        # 2. Teste de Leitura (Tabela 'pipes' deve existir se o usuário criou, ou podemos tentar listar)
        # Vamos tentar ler a tabela 'pipes' (se não existir, vai dar erro, o que é um bom teste)
        print("Tentando ler tabela 'pipes'...")
        response = supabase.table("pipes").select("*").limit(1).execute()
        print(f"Leitura bem-sucedida! Dados: {response.data}")
        
        # 3. Teste de Escrita (Upsert em tabela de teste se possível, ou apenas confiar na leitura)
        # Como não queremos sujar o banco, vamos ficar apenas na leitura por enquanto.
        # Se a leitura funcionou, a autenticação e conexão estão OK.
            
        print("✅ Teste de conexão completo com sucesso!")
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")

if __name__ == "__main__":
    test_connection()
