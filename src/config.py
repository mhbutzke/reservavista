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

# CONSTANTES
MAX_RETRIES = 5
REQUEST_DELAY = 0.5
BACKOFF_FACTOR = 1.5

if not os.path.exists(CSV_OUTPUT_DIR):
    os.makedirs(CSV_OUTPUT_DIR)

if not VISTA_API_KEY or not VISTA_API_URL:
    print("AVISO: VISTA_API_KEY e VISTA_API_URL precisam ser definidos no arquivo .env para funcionamento correto.")
