# 🔌 Guia de Integração - BI Frontend com RLS

Este guia explica como atualizar seu BI frontend para funcionar com Row Level Security (RLS) habilitado.

---

## ⚠️ O Problema

Após habilitar RLS, seu BI frontend **NÃO conseguirá mais acessar os dados** usando a chave `anon` (pública).

**Erro esperado:**
```json
{
  "code": "PGRST200",
  "message": "The result contains 0 rows"
}
```

Ou simplesmente retornará arrays vazios `[]`.

---

## ✅ Soluções

Você tem **3 opções** para resolver isso:

### Opção 1: Usar Service Role Key (Recomendado para BI Interno)

> [!WARNING]
> **Service Role Key bypassa TODAS as políticas RLS!**  
> Use apenas em ambientes seguros (backend, servidor interno, BI interno).

#### Implementação

**Se seu BI é uma aplicação backend (Node.js, Python, etc):**

```javascript
// Antes (com anon key)
const supabase = createClient(
  'https://seu-projeto.supabase.co',
  'sua_anon_key_aqui' // ❌ Não funciona mais
)

// Depois (com service role key)
const supabase = createClient(
  'https://seu-projeto.supabase.co',
  process.env.SUPABASE_SERVICE_ROLE_KEY // ✅ Funciona!
)
```

**Onde obter a Service Role Key:**
1. Supabase Dashboard → Settings → API
2. Copiar **`service_role`** key (não a `anon`)
3. Configurar como variável de ambiente

**⚠️ NUNCA exponha a service_role key no frontend!**

---

### Opção 2: Criar Políticas RLS Específicas para BI

Se seu BI roda no frontend (React, Vue, etc) ou você quer mais segurança, crie políticas específicas.

#### Exemplo: Permitir Leitura Pública de Dados Agregados

```sql
-- Permitir leitura de dados não sensíveis
CREATE POLICY "Public read access to negocios"
  ON negocios
  FOR SELECT
  USING (true); -- Permite leitura para todos

-- Permitir leitura de clientes (sem dados sensíveis)
CREATE POLICY "Public read access to clientes"
  ON clientes
  FOR SELECT
  USING (true);
```

#### Exemplo: Permitir Apenas Usuários Autenticados

```sql
-- Apenas usuários logados
CREATE POLICY "Authenticated users can read negocios"
  ON negocios
  FOR SELECT
  USING (auth.role() = 'authenticated');
```

#### Exemplo: Filtrar por Agência do Usuário

```sql
-- Cada usuário vê apenas dados da sua agência
CREATE POLICY "Users see only their agency data"
  ON negocios
  FOR SELECT
  USING (
    "CodigoAgencia" = (
      SELECT "CodigoAgencia" 
      FROM usuarios 
      WHERE email = auth.email()
    )
  );
```

---

### Opção 3: Criar API Intermediária

Criar um endpoint backend que:
1. Usa service role para buscar dados
2. Aplica suas próprias regras de acesso
3. Expõe dados filtrados para o frontend

**Exemplo (Node.js/Express):**

```javascript
// backend/api/dashboard.js
app.get('/api/dashboard/stats', async (req, res) => {
  // Service role client (servidor)
  const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
  );
  
  // Buscar dados
  const { data, error } = await supabase
    .from('negocios')
    .select('*')
    .gte('DataCadastro', '2025-01-01');
  
  if (error) return res.status(500).json({ error });
  
  // Aplicar lógica de negócio/filtros
  const stats = calculateStats(data);
  
  res.json(stats);
});
```

---

## 🎯 Qual Opção Escolher?

| Situação | Solução Recomendada |
|----------|---------------------|
| BI é aplicação backend/servidor | **Opção 1** - Service Role |
| BI roda no navegador (frontend) | **Opção 2** - Políticas RLS |
| Precisa de lógica complexa de acesso | **Opção 3** - API Intermediária |
| Dados são completamente públicos | **Opção 2** - RLS com `USING (true)` |
| Diferentes usuários veem dados diferentes | **Opção 2** - RLS com filtros |

---

## 🔧 Guia Passo-a-Passo (Opção 1 - Recomendado)

### Passo 1: Obter Service Role Key

```bash
# 1. Acessar Supabase Dashboard
# 2. Settings → API
# 3. Copiar "service_role" secret key
```

### Passo 2: Configurar no BI

**Para aplicação backend:**

```bash
# Adicionar ao .env
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...SUA_KEY_AQUI
```

**Para Docker Compose:**

```yaml
services:
  bi-backend:
    environment:
      - SUPABASE_URL=https://seu-projeto.supabase.co
      - SUPABASE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
```

**Para aplicação Node.js:**

```javascript
// config/supabase.js
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);
```

**Para aplicação Python:**

```python
# config.py
import os
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(supabase_url, supabase_key)
```

### Passo 3: Testar

```bash
# Testar query
curl -X GET 'https://seu-projeto.supabase.co/rest/v1/negocios?select=*&limit=5' \
  -H "apikey: SUA_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer SUA_SERVICE_ROLE_KEY"
```

**Resultado esperado:** JSON com 5 negócios ✅

---

## 🛡️ Segurança - Boas Práticas

### ✅ DO (Faça)

- ✅ Use service role **apenas em backend**
- ✅ Armazene em variáveis de ambiente
- ✅ Adicione `.env` ao `.gitignore`
- ✅ Use HTTPS para todas as requisições
- ✅ Implemente rate limiting no seu BI
- ✅ Adicione autenticação no BI (login de usuários)

### ❌ DON'T (Não Faça)

- ❌ Nunca exponha service role no frontend JavaScript
- ❌ Nunca commite service role no Git
- ❌ Nunca envie service role em URLs
- ❌ Nunca logue service role em logs
- ❌ Nunca compartilhe service role por email/chat

---

## 🧪 Checklist de Migração

- [ ] Identifiquei qual opção usar (1, 2 ou 3)
- [ ] Obtive a Service Role Key do Supabase
- [ ] Configurei a key como variável de ambiente
- [ ] Atualizei o código do BI para usar nova key
- [ ] Testei queries básicas (SELECT)
- [ ] Testei queries com filtros
- [ ] Testei queries com JOINs
- [ ] Verifiquei que dados sensíveis não são expostos
- [ ] Adicionei rate limiting (se aplicável)
- [ ] Documentei mudança para a equipe

---

## 🐛 Troubleshooting

### Problema: "The result contains 0 rows"

**Causa**: Ainda usando anon key ou RLS está bloqueando.

**Solução**:
```sql
-- Verificar se está usando service role
SELECT current_user, current_role;
-- Deve retornar: service_role

-- Se retornar anon, você está usando anon key ainda
```

### Problema: "permission denied for table X"

**Causa**: Service role não tem permissão (raro).

**Solução**:
```sql
-- Garantir que service role tem permissões
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
```

### Problema: "Invalid API key"

**Causa**: Key incorreta ou expirada.

**Solução**:
1. Regenere a service role key no dashboard
2. Atualize em todos os lugares que usa

### Problema: BI muito lento após RLS

**Causa**: Consultas complexas com policies.

**Solução**:
- Use service role (bypassa RLS completamente)
- Ou otimize as políticas RLS
- Ou crie índices nas colunas filtradas

---

## 📞 Suporte

Se precisar de ajuda:
1. Verifique se está usando a **service_role** key (não anon)
2. Teste a key via curl (comando na seção "Testar")
3. Verifique logs do BI para mensagens de erro específicas
4. Consulte [Supabase RLS Docs](https://supabase.com/docs/guides/auth/row-level-security)

---

## 📝 Exemplo Completo - Dashboard Metabase

Se você usa Metabase, siga estes passos:

1. **Settings → Admin → Databases**
2. **Edit** seu database Supabase
3. No campo **Additional JDBC connection string options**, adicione:
   ```
   &apikey=SUA_SERVICE_ROLE_KEY_AQUI
   ```
4. **Save** e teste conexão

**Ou configure via PostgreSQL direto:**

1. **Database Type**: PostgreSQL
2. **Host**: db.seu-projeto.supabase.co
3. **Port**: 5432
4. **Database**: postgres
5. **Username**: postgres
6. **Password**: (sua senha do Supabase)
7. **Use SSL**: Yes

Isso conecta direto no PostgreSQL, bypassando APIs e RLS.

---

**Última atualização**: 2025-12-10  
**Versão**: 1.0
