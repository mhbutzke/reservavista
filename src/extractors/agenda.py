from src.utils.async_api_client import get_vista_data_async
from src.utils.supabase_client import get_last_run_from_supabase, update_last_run_in_supabase, save_to_supabase

async def extract_agenda(session):
    print("\n--- Extraindo Agenda (Async) ---")
    fields = [
        "Codigo", "Assunto", "DataHoraInicio", "DataHoraFinal", "DataHora", "DataHoraAtualizacao", 
        "Local", "Responsavel", "Corretor", "Cliente", "NomeCliente", "Imovel", "Negocio", 
        "NomeNegocio", "Status", "Concluido", "Tipo", "TipoAtividade", "Tarefa", "Prioridade", 
        "DiaInteiro", "AlertaMinutos", "Grupo", "Particular", "MotivoCancelamentoVisita", 
        "SmsCliente", "SmsProprietario", "CodigoAtividade", "Texto"
    ]
    
    # Agenda endpoint usually supports pagination
    agenda_items = await get_vista_data_async(session, "agenda/listar", fields)
    print(f"Total de itens de agenda extraídos: {len(agenda_items)}")
    
    if agenda_items:
        save_to_supabase(agenda_items, "agenda", unique_key="Codigo")
        update_last_run_in_supabase("agenda")
        
    return agenda_items
