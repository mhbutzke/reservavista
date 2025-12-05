from etl_prototype import extract_usuarios, extract_agencias, extract_proprietarios, extract_corretores, extract_pipes
import os
from dotenv import load_dotenv

# Ensure env vars are loaded for the imported module
load_dotenv()

def main():
    print("Starting verification of new entities...")
    
    try:
        extract_usuarios()
        print("✅ Usuarios extracted")
    except Exception as e:
        print(f"❌ Usuarios failed: {e}")

    try:
        extract_agencias()
        print("✅ Agencias extracted")
    except Exception as e:
        print(f"❌ Agencias failed: {e}")

    try:
        extract_proprietarios()
        print("✅ Proprietarios extracted")
    except Exception as e:
        print(f"❌ Proprietarios failed: {e}")

    try:
        extract_corretores()
        print("✅ Corretores extracted")
    except Exception as e:
        print(f"❌ Corretores failed: {e}")

    try:
        extract_pipes()
        print("✅ Pipes extracted")
    except Exception as e:
        print(f"❌ Pipes failed: {e}")

if __name__ == "__main__":
    main()
