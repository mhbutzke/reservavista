# 🔒 Guia de Configuração de Segurança (SIMPLIFICADO)

Este guia detalha os passos necessários para implementar as correções de segurança.

> [!NOTE]
> **Versão Simplificada**: Sem criptografia de CPF (dados de uso interno).  
> Foco em RLS e Audit Logging.

---

## 📋 Pré-requisitos

- [ ] Acesso ao projeto Supabase (owner/admin)
- [ ] Acesso ao repositório GitHub (admin)
- [ ] Python 3.9+ instalado
- [ ] Acesso ao BI Frontend (para atualização)

---

## 🚀 Passo 1: Atualizar Dependências

```bash
cd "/Users/mhbutzke/Documents/Reserva Imob/API v4"

# Instalar novas dependências
pip install -r requirements.txt

# Verificar vulnerabilidades
safety check
```

---

## 🔑 Passo 2: Obter Service Role Key do Supabase

1. Acesse o [Supabase Dashboard](https://supabase.com/dashboard)
2. Selecione seu projeto
3. Vá em **Settings** → **API**
4. Copie a `service_role` key (não a `anon` key)
   - ⚠️ **Service role bypassa RLS** - Use apenas no backend!
   
5. Anote também a `Project URL`

---

## 🔧 Passo 3: Configurar Secrets no GitHub

1. Vá para o repositório no GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione o seguinte secret:

| Secret Name | Valor |
|-------------|-------|
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key do Supabase |

> **Secrets existentes** (já devem estar configurados):
> - `VISTA_API_KEY`
> - `VISTA_API_URL`
> - `SUPABASE_URL`

---

## 💾 Passo 4: Aplicar Migrations no Supabase

### 4.1 Fazer Backup

1. No Supabase Dashboard: **Database** → **Backups**
2. Clique em **Create backup now**
3. Aguarde conclusão

### 4.2 Aplicar Migration 001 - RLS

1. No Supabase Dashboard: **SQL Editor**
2. Clique em **New query**
3. Cole o conteúdo de `migrations/001_enable_rls.sql`
4. Clique em **Run**
5. Verifique que não houve erros

> [!CAUTION]
> **Após executar esta migration, seu BI frontend PARARÁ de funcionar temporariamente!**  
> Isso é esperado - você configurará no Passo 6.

### 4.3 Aplicar Migration 002 - Audit Logs

1. Cole o conteúdo de `migrations/002_audit_logs_simplified.sql`
2. Clique em **Run**

---

## 🧪 Passo 5: Testar Localmente

### 5.1 Atualizar .env Local

Crie/atualize arquivo `.env`:

```env
VISTA_API_URL=sua_url_vista
VISTA_API_KEY=sua_chave_vista
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=SUA_SERVICE_ROLE_KEY_AQUI
ENABLE_DATA_VALIDATION=True
ENABLE_AUDIT_LOGGING=True
```

### 5.2 Executar Testes de Segurança

```bash
# Instalar pytest
pip install pytest

# Executar testes
pytest tests/test_security.py -v
```

Todos os testes devem passar ✅

### 5.3 Testar ETL Localmente

```bash
# Executar ETL
python -m src.main
```

Verifique:
- ✅ Não há erros de autenticação
- ✅ Dados são salvos com sucesso
- ✅ Logs não exibem CPF/emails completos
- ✅ Registros aparecem na tabela `audit_logs`

---

## 🔌 Passo 6: Atualizar BI Frontend

> [!IMPORTANT]
> **SEU BI PRECISA SER ATUALIZADO!**  
> Siga o guia completo: [docs/BI_INTEGRATION.md](file:///Users/mhbutzke/Documents/Reserva%20Imob/API%20v4/docs/BI_INTEGRATION.md)

### Opção Rápida (Recomendado):

Se seu BI é backend, atualize para usar Service Role Key:

```javascript
// Antes
const supabase = createClient(url, 'anon_key')

// Depois
const supabase = createClient(url, process.env.SUPABASE_SERVICE_ROLE_KEY)
```

**⚠️ Consulte o guia completo para sua tecnologia específica!**

---

## 🔍 Passo 7: Verificar RLS

### 7.1 Testar Bloqueio Público

```bash
# Tentar acessar com chave anon (deve falhar)
curl -X GET 'https://SEU_PROJETO.supabase.co/rest/v1/clientes?select=*' \
  -H "apikey: SUA_ANON_KEY" \
  -H "Authorization: Bearer SUA_ANON_KEY"
```

**Resultado esperado**: Array vazio `[]` ou erro 403 ✅

### 7.2 Verificar Service Role

```bash
# Acessar com service role (deve funcionar)
curl -X GET 'https://SEU_PROJETO.supabase.co/rest/v1/clientes?select=*&limit=5' \
  -H "apikey: SUA_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer SUA_SERVICE_ROLE_KEY"
```

**Resultado esperado**: JSON com 5 clientes ✅

### 7.3 Verificar Audit Logs

No SQL Editor:

```sql
SELECT * FROM audit_logs 
ORDER BY timestamp DESC 
LIMIT 10;
```

Se vazio, execute o ETL primeiro.

---

## 🚢 Passo 8: Deploy em Produção

### 8.1 Commit e Push

```bash
git add .
git commit -m "feat: implement security improvements - RLS, validation, audit logging"
git push origin main
```

### 8.2 Monitorar Workflow

1. Vá para **Actions** no GitHub
2. Aguarde workflow `Vista CRM to Supabase ETL` completar
3. Verifique que não há erros

### 8.3 Verificar Audit Logs em Produção

No Supabase SQL Editor:

```sql
SELECT * FROM audit_logs 
ORDER BY timestamp DESC 
LIMIT 10;
```

Você deve ver registros da última execução do ETL.

---

## ✅ Checklist Final

- [ ] Todas dependências instaladas
- [ ] Service Role Key configurada no GitHub
- [ ] Migration 001 (RLS) aplicada com sucesso
- [ ] Migration 002 (Audit Logs) aplicada
- [ ] Testes de segurança passando
- [ ] ETL funcionando localmente
- [ ] RLS bloqueando acesso público
- [ ] Service Role permitindo acesso do ETL
- [ ] Audit logs sendo criados
- [ ] **BI Frontend atualizado e funcionando**
- [ ] Workflow GitHub Actions passando
- [ ] Logs não exibindo dados sensíveis

---

## 🆘 Troubleshooting

### Erro: "SUPABASE_KEY obrigatório"

**Causa**: Variável de ambiente não configurada.

**Solução**:
```bash
# Verificar .env
cat .env | grep SUPABASE_KEY

# Se vazio, adicionar
echo "SUPABASE_KEY=sua_service_role_key" >> .env
```

### Erro: "Context access might be invalid: SUPABASE_SERVICE_ROLE_KEY"

**Causa**: Secret não existe no GitHub.

**Solução**: Vá para GitHub → Settings → Secrets e adicione `SUPABASE_SERVICE_ROLE_KEY`.

### ETL funciona mas não salva dados

**Causa**: RLS está bloqueando. Provavelmente usando ANON key.

**Solução**:
1. Verifique que está usando `SUPABASE_SERVICE_ROLE_KEY`
2. No dashboard, Settings → API, confirme que copiou a `service_role` key

### BI Frontend retorna dados vazios

**Causa**: BI ainda está usando anon key.

**Solução**: Consulte [docs/BI_INTEGRATION.md](file:///Users/mhbutzke/Documents/Reserva%20Imob/API%20v4/docs/BI_INTEGRATION.md)

---

## 📞 Suporte

Se encontrar problemas:
1. Consulte o arquivo `SECURITY.md` para mais detalhes
2. Verifique os logs de audit: `SELECT * FROM audit_logs WHERE status = 'ERROR'`
3. Para BI: Consulte `docs/BI_INTEGRATION.md`

---

## 📚 Próximos Passos

Após implementação bem-sucedida:

1. **Configurar Monitoramento**
   - Setup de alertas para erros de ETL
   - Dashboard de métricas

2. **Documentar Processos**
   - Procedimento de rotação de chaves
   - Runbook de incidentes

3. **Agendar Revisões**
   - Trimestral: Revisar políticas de segurança
   - Mensal: Audit de vulnerabilidades (safety check)

---

**Boa sorte! 🚀**

**Tempo estimado**: 1-2 horas (muito mais rápido sem criptografia!)
