
import os
import asyncio
from src.utils.supabase_client import get_supabase_client

def query_lost_clients():
    supabase = get_supabase_client()
    
    # Query to find clients
    # We join negocios and atividades.
    # Since Supabase client might not support complex joins easily via the JS-like API if relations aren't perfect,
    # we might need to use RPC or raw SQL if possible.
    # But the python client supports .rpc() or we can fetch and filter.
    # Given the likely size, fetching all might be slow.
    # Let's try to use the .rpc() if there was a function, but there isn't one for this.
    # However, we can use the postgrest 'filter' capabilities.
    
    # Actually, the user asked to "search in the activities table".
    # Let's try to fetch activities that match the criteria first, then get the deals/clients.
    
    print("Fetching activities with 'Visita' or 'Proposta'...")
    
    # We need to filter by EtapaAcao or TipoAtividade.
    # And we need the deal status to be 'Perdido'.
    # We can't easily join in the client without a view or foreign keys set up for auto-detection.
    
    # Let's try a raw SQL query if the client allows it?
    # The client exposes .table()... but maybe not raw sql directly unless we use a specific method.
    # The `supabase-py` client is a wrapper around postgrest.
    
    # Alternative: Fetch all lost deals first.
    print("Fetching lost deals...")
    response_deals = supabase.table("negocios").select("Codigo, CodigoCliente, NomeCliente").eq("Status", "Perdido").execute()
    lost_deals = response_deals.data
    
    if not lost_deals:
        print("No lost deals found.")
        return

    lost_deal_ids = [d["Codigo"] for d in lost_deals]
    print(f"Found {len(lost_deals)} lost deals.")
    
    # Now fetch activities for these deals that match 'Visita' or 'Proposta'
    # We might need to chunk this if there are too many IDs.
    
    clients_found = {}
    
    batch_size = 100
    for i in range(0, len(lost_deal_ids), batch_size):
        batch_ids = lost_deal_ids[i:i+batch_size]
        
        # Filter activities
        # We want: CodigoNegocio IN batch_ids AND (EtapaAcao ILIKE '%Visita%' OR ...)
        # Postgrest syntax for OR is a bit tricky with AND.
        # .or_() method.
        
        # "CodigoNegocio.in.(...),and(or(EtapaAcao.ilike.*Visita*,EtapaAcao.ilike.*Proposta*,TipoAtividade.ilike.*Visita*,TipoAtividade.ilike.*Proposta*))"
        # This is complicated to construct with the builder.
        
        # Simpler approach: Fetch all activities for these deals and filter in python.
        # Or just fetch activities with Visita/Proposta and filter by deal ID in python?
        # Fetching activities by deal ID is safer.
        
        response_activities = supabase.table("atividades") \
            .select("CodigoNegocio, EtapaAcao, TipoAtividade") \
            .in_("CodigoNegocio", batch_ids) \
            .execute()
            
        activities = response_activities.data
        
        for act in activities:
            etapa = str(act.get("EtapaAcao") or "").lower()
            tipo = str(act.get("TipoAtividade") or "").lower()
            
            if "visita" in etapa or "proposta" in etapa or "visita" in tipo or "proposta" in tipo:
                deal_id = act["CodigoNegocio"]
                # Find the client for this deal
                deal = next((d for d in lost_deals if d["Codigo"] == deal_id), None)
                if deal:
                    client_id = deal.get("CodigoCliente")
                    client_name = deal.get("NomeCliente")
                    if client_id:
                        clients_found[client_id] = client_name
        
        print(f"Processed batch {i//batch_size + 1}, found {len(clients_found)} unique clients so far...")

    print("\n--- Clients Found ---")
    for cid, name in clients_found.items():
        print(f"{name} (ID: {cid})")

if __name__ == "__main__":
    query_lost_clients()
