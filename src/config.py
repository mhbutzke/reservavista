import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# API VISTA
VISTA_API_URL = os.getenv("VISTA_API_URL")
if VISTA_API_URL and not VISTA_API_URL.startswith("http"):
    VISTA_API_URL = f"https://{VISTA_API_URL}"

VISTA_API_KEY = os.getenv("VISTA_API_KEY")

# SUPABASE
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# CONFIGURAÇÕES GERAIS
SAVE_TO_CSV = os.getenv("SAVE_TO_CSV", "False").lower() == "true"
CSV_OUTPUT_DIR = os.getenv("CSV_OUTPUT_DIR", "./data")

# CONFIGURAÇÕES DE SEGURANÇA
ENABLE_DATA_VALIDATION = os.getenv("ENABLE_DATA_VALIDATION", "True").lower() == "true"
ENABLE_AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "True").lower() == "true"

# CONSTANTES
MAX_RETRIES = 5
REQUEST_DELAY = 0.5
BACKOFF_FACTOR = 1.5
REQUEST_TIMEOUT = 30  # segundos

if not os.path.exists(CSV_OUTPUT_DIR):
    os.makedirs(CSV_OUTPUT_DIR)

# VALIDAÇÃO OBRIGATÓRIA DE CREDENCIAIS
if not VISTA_API_KEY or not VISTA_API_URL:
    raise ValueError(
        "ERRO CRÍTICO: VISTA_API_KEY e VISTA_API_URL são obrigatórios. "
        "Configure no arquivo .env"
    )

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "ERRO CRÍTICO: SUPABASE_URL e SUPABASE_KEY são obrigatórios. "
        "Configure no arquivo .env"
    )

# AVISO: Service Role Key
if SUPABASE_KEY and not SUPABASE_KEY.startswith("eyJ"):
    print("AVISO: Certifique-se de estar usando a SERVICE_ROLE key, não a ANON key!")

print("✓ Configuração carregada com sucesso")
print(f"✓ Validação de dados: {'HABILITADA' if ENABLE_DATA_VALIDATION else 'DESABILITADA'}")
print(f"✓ Audit logging: {'HABILITADO' if ENABLE_AUDIT_LOGGING else 'DESABILITADO'}")
