# Security Policy

## 🔒 Política de Segurança - Vista CRM ETL

### Reporting Security Issues

Se você descobrir uma vulnerabilidade de segurança, por favor **NÃO** abra uma issue pública. Em vez disso:

1. Entre em contato diretamente com a equipe através de: [SEU_EMAIL_SEGURANÇA]
2. Inclua o máximo de detalhes possível:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
   - Sugestões de correção (se houver)

Você receberá uma resposta dentro de 48 horas e atualizações regulares sobre o progresso da correção.

---

## 🛡️ Medidas de Segurança Implementadas

### 1. Row Level Security (RLS)
- ✅ RLS habilitado em todas as tabelas do Supabase
- ✅ Políticas de acesso restritivas (apenas service role)
- ✅ Bloqueio de acesso público por padrão

### 2. Criptografia de Dados Sensíveis
- ✅ CPF, CNPJ e RG criptografados usando pgcrypto
- ✅ Chave de criptografia armazenada em variáveis de ambiente
- ✅ Funções de encrypt/decrypt seguras

### 3. Validação e Sanitização
- ✅ Validação de CPF/CNPJ com algoritmo correto
- ✅ Sanitização de inputs para prevenir XSS
- ✅ Proteção contra SQL injection

### 4. Logging Seguro
- ✅ Dados sensíveis automaticamente redatados dos logs
- ✅ Audit logging de todas operações
- ✅ Rastreabilidade completa (LGPD compliance)

### 5. Infraestrutura
- ✅ Dependências com versões fixas
- ✅ Verificação automática de vulnerabilidades (Safety)
- ✅ Timeouts em todas requisições HTTP
- ✅ Rate limiting

---

## 🔑 Gestão de Credenciais

###Secrets no GitHub Actions
Os seguintes secrets devem ser configurados:

| Secret | Descrição | Tipo |
|--------|-----------|------|
| `VISTA_API_KEY` | Chave de API do Vista CRM | API Key |
| `VISTA_API_URL` | URL da API do Vista | URL |
| `SUPABASE_URL` | URL do projeto Supabase | URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service Role Key do Supabase | API Key |
| `ENCRYPTION_KEY` | Chave para criptografia de dados | String Segura |

### Rotação de Chaves

**Frequência Recomendada:**
- API Keys: A cada 90 dias
- Encryption Key: A cada 180 dias (requer re-criptografia de dados)

**Processo de Rotação:**
1. Gerar nova chave
2. Atualizar GitHub Secret
3. Testar em ambiente de staging
4. Deploy em produção
5. Revogar chave antiga

---

## 📋 Compliance LGPD

### Dados Pessoais Processados
- CPF/CNPJ
- RG
- Nome completo
- Endereço
- Email
- Telefone
- Data de nascimento

### Medidas de Proteção
1. **Criptografia**: Dados sensíveis armazenados criptografados
2. **Minimização**: Apenas dados necessários são coletados
3. **Auditoria**: Logs de todas operações
4. **Retenção**: Dados mantidos por tempo necessário
5. **Acesso**: Restrito apenas a serviços autorizados

### Direitos do Titular
Para exercer direitos LGPD (acesso, correção, exclusão), entre em contato através de: [SEU_EMAIL_LGPD]

---

## 🚨 Resposta a Incidentes

### Plano de Ação

**1. Detecção (0-2h)**
- Monitorar alertas de segurança
- Identificar o escopo do incidente
- Documentar descobertas iniciais

**2. Contenção (2-4h)**
- Isolar sistemas afetados
- Revogar credenciais comprometidas
- Bloquear acessos não autorizados

**3. Erradicação (4-24h)**
- Corrigir vulnerabilidade explorada
- Atualizar dependências
- Aplicar patches de segurança

**4. Recuperação (24-48h)**
- Restaurar serviços
- Verificar integridade dos dados
- Testar correções

**5. Pós-Incidente (1 semana)**
- Análise de causa raiz
- Atualizar políticas
- Treinar equipe
- Notificar autoridades (se necessário)

### Contatos de Emergência
- **Segurança**: [EMAIL]
- **Técnico**: [EMAIL]
- **Compliance**: [EMAIL]

---

## ✅ Checklist de Segurança para Deploy

Antes de deployar qualquer mudança:

- [ ] Todas dependências estão atualizadas
- [ ] Safety check passou (sem vulnerabilidades)
- [ ] Testes de segurança passaram
- [ ] Secrets estão configurados corretamente
- [ ] RLS está habilitado
- [ ] Audit logging está funcionando
- [ ] Dados sensíveis estão criptografados
- [ ] Logs não contêm dados sensíveis
- [ ] Backups estão configurados
- [ ] Monitoramento está ativo

---

## 📚 Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Guia LGPD](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)
- [Supabase Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## 📝 Histórico de Atualizações

| Data | Versão | Mudanças |
|------|--------|----------|
| 2025-12-10 | 1.0.0 | Política inicial de segurança |

---

**Última atualização**: 2025-12-10  
**Próxima revisão**: 2026-03-10 (trimestral)
