#!/bin/bash

# Navegar para o diretório do projeto
cd "/Users/mhbutzke/Documents/Reserva Imob/API v4"

# Ativar ambiente virtual (se existir) ou usar python3 do sistema
# Ajuste o caminho do python se necessário
/usr/bin/python3 scripts/sync_activities.py >> logs/activities_etl_$(date +\%Y\%m\%d).log 2>&1
