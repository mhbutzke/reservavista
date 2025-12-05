import os
import requests
from dotenv import load_dotenv

load_dotenv()

VISTA_API_KEY = os.getenv("VISTA_API_KEY")
VISTA_API_URL = os.getenv("VISTA_API_URL")

if VISTA_API_URL and not VISTA_API_URL.startswith("http"):
    VISTA_API_URL = f"http://{VISTA_API_URL}"

def check_fields(endpoint):
    url = f"{VISTA_API_URL}/{endpoint}"
    params = {
        "key": VISTA_API_KEY,
        "pesquisa": '{"fields":["*"]}' # Tentar buscar tudo ou ver se retorna erro com lista
    }
    headers = {"Accept": "application/json"}
    
    try:
        print(f"Consultando {endpoint}...")
        response = requests.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        try:
            print(response.json())
        except:
            print(response.text)
    except Exception as e:
        print(e)

def list_fields(endpoint):
    # Tentar endpoint específico de campos se existir
    url = f"{VISTA_API_URL}/{endpoint}"
    params = {
        "key": VISTA_API_KEY
    }
    headers = {"Accept": "application/json"}
    try:
        print(f"Consultando {endpoint}...")
        response = requests.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        print(response.text)
    except Exception as e:
        print(e)

def inspect_negocios():
    endpoint = "negocios/detalhes"
    url = f"{VISTA_API_URL}/{endpoint}"
    # Tentar buscar detalhes do negocio 6
    params = {
        "key": VISTA_API_KEY,
        "codigo_negocio": "6"
    }
    headers = {"Accept": "application/json"}
    
    try:
        print(f"Inspecionando {endpoint} id=6...")
        response = requests.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Listar campos das novas entidades
    print("--- USUARIOS ---")
    list_fields("usuarios/listarcampos")
    
    print("\n--- AGENCIAS ---")
    list_fields("agencias/listarcampos")
    
    print("\n--- CORRETORES ---")
    list_fields("corretores/listarcampos")
    
    print("\n--- PIPES ---")
    # Pipes pode não ter listarcampos, vamos tentar listar para ver a estrutura
    list_fields("pipes/listar")
    list_fields("pipes/etapas")
