import asyncio
import aiohttp
import json
from src.utils.async_api_client import make_async_api_request, get_vista_data_async
from src.config import VISTA_API_KEY

async def inspect_api():
    async with aiohttp.ClientSession() as session:
        print("\n--- Verifying IDs and Empresa Field ---")
        
        # 1. Fetch Usuarios that are Corretores
        fields_u = ["Codigo", "Nome", "Corretor", "Gerente", "Empresa"]
        filters_u = {"Corretor": "Sim"}
        usuarios = await get_vista_data_async(session, "usuarios/listar", fields=fields_u, filters=filters_u, items_per_page=5)
        print("Usuarios (Corretores):")
        print(json.dumps(usuarios[:3], indent=2, ensure_ascii=False))
        
        # 2. Fetch Corretores
        corretores = await get_vista_data_async(session, "corretores/listar", fields=["Codigo", "Nome"], items_per_page=5)
        print("\nCorretores:")
        print(json.dumps(corretores[:3], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect_api())
