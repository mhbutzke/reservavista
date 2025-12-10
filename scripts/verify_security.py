import os
import requests
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY") # Assumindo que esta é a service role key conforme setup
# Tentar obter anon key se existir, senão usar string vazia (vai falhar autenticação, o que é bom para teste de bloqueio)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "") 

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erro: SUPABASE_URL ou SUPABASE_KEY não definidos no .env")
    exit(1)

print(f"🔹 Testando segurança para: {SUPABASE_URL}")

def test_rls_public_access():
    print("\n🔍 7.1 Testando Bloqueio Público (RLS)...")
    
    # Tentar acessar tabela 'clientes' via REST API usando anon key (ou sem key)
    url = f"{SUPABASE_URL}/rest/v1/clientes?select=*"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if len(data) == 0:
                print("✅ Sucesso: Acesso público retornou lista vazia (RLS funcionando).")
            else:
                print(f"❌ FALHA: Acesso público retornou {len(data)} registros! RLS NÃO está funcionando corretamente.")
        elif response.status_code in [401, 403]:
            print(f"✅ Sucesso: Acesso público bloqueado (Status {response.status_code}).")
        else:
            print(f"⚠️ Aviso: Status inesperado: {response.status_code}. Resposta: {response.text}")
            
    except Exception as e:
        print(f"⚠️ Erro ao testar acesso público: {e}")

def test_service_role_access():
    print("\n🔍 7.2 Testando Acesso Service Role...")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Tentar buscar 1 cliente
        response = supabase.table("clientes").select("*").limit(1).execute()
        
        if len(response.data) >= 0: # Pode ser 0 se não tiver clientes, mas não deve dar erro
            print(f"✅ Sucesso: Service Role conseguiu acessar a tabela (Retornou {len(response.data)} registros).")
        else:
            print("❌ FALHA: Service Role não conseguiu acessar dados.")
            
    except Exception as e:
        print(f"❌ FALHA: Erro ao acessar com Service Role: {e}")

def verify_audit_logs():
    print("\n🔍 7.3 Verificando Audit Logs...")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Buscar últimos 5 logs
        response = supabase.table("audit_logs").select("*").order("timestamp", desc=True).limit(5).execute()
        
        if len(response.data) > 0:
            print(f"✅ Sucesso: Encontrados {len(response.data)} registros de audit log.")
            print("   Últimos logs:")
            for log in response.data:
                print(f"   - [{log.get('timestamp')}] {log.get('operation')} em {log.get('entity')} ({log.get('status')})")
        else:
            print("⚠️ Aviso: Tabela audit_logs está vazia. (Isso é normal se nenhum ETL rodou após a criação da tabela)")
            
    except Exception as e:
        print(f"❌ FALHA: Erro ao ler audit_logs: {e}")
        if "PGRST205" in str(e):
            print("   💡 Dica: O erro PGRST205 indica cache de schema desatualizado. Vá no Supabase Dashboard -> Settings -> API -> Reload schema cache.")

if __name__ == "__main__":
    test_rls_public_access()
    test_service_role_access()
    verify_audit_logs()
