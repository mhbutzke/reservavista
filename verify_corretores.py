import asyncio
import aiohttp
import json
from src.extractors.outros import extract_corretores

async def verify_corretores():
    async with aiohttp.ClientSession() as session:
        corretores = await extract_corretores(session)
        print(json.dumps(corretores[:3], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(verify_corretores())
