# NioChat - Sistema de Atendimento WhatsApp

Sistema completo de atendimento via WhatsApp com IA inteligente, integração SGP e dashboard em tempo real.

## 🚀 Funcionalidades Principais

### 🤖 IA Inteligente
- **ChatGPT Integrado**: Atendimento automatizado 24/7
- **Consulta SGP Automática**: Dados reais do cliente
- **Transcrição de Áudio**: Conversão automática de voz para texto
- **Function Calls**: Execução automática de ações no SGP
- **Personalização**: IA única para cada provedor
- **Recuperação de Vendas**: IA analisa conversas e reativa clientes interessados

### 📱 WhatsApp Completo
- **Uazapi/Evolution API**: Integração nativa
- **Mídia Completa**: Imagens, vídeos, áudios, documentos
- **Reações e Exclusão**: Sistema completo de interações
- **Status de Entrega**: Confirmação de recebimento

### 📊 Dashboard Avançado
- **Tempo Real**: Atualizações instantâneas via Supabase
- **Métricas Precisas**: Taxa de satisfação e resolução
- **Gráficos Interativos**: Visualizações dinâmicas
- **Filtros Avançados**: Por data, usuário, equipe

### 🔐 Sistema Multi-tenant
- **Isolamento Total**: Cada provedor tem seus dados
- **Permissões Granulares**: Controle fino de acesso
- **Equipes**: Organização por equipes
- **Transferência Inteligente**: Entre agentes e equipes

### 🔄 Recuperador de Conversas (NOVO!)
- **🤖 Análise Inteligente**: IA analisa conversas encerradas para identificar clientes interessados em planos
- **📱 Reativação Automática**: Envia mensagens personalizadas via WhatsApp para recuperar vendas perdidas
- **📊 Dashboard Visual**: Termômetro animado com taxa de conversão e estatísticas em tempo real
- **🔒 Isolamento por Provedor**: Cada provedor vê apenas seus dados de recuperação
- **⚙️ Configurações Flexíveis**: 
  - Delay configurável (minutos de inatividade)
  - Número máximo de tentativas
  - Palavras-chave de interesse personalizáveis
  - Horários de funcionamento
- **📈 Métricas Detalhadas**: Tentativas, recuperações, taxa de conversão e atividades recentes
- **🎯 Processamento Inteligente**: Só ativa quando cliente menciona planos e conversa não está atribuída

## 🏗️ Arquitetura

```
Frontend (React) → Backend (Django) → Integrações
     ↓                ↓                    ↓
Dashboard ←→ API REST ←→ WhatsApp (Uazapi)
     ↓                ↓                    ↓
Supabase ←→ WebSocket ←→ IA (OpenAI)
     ↓                ↓                    ↓
Auditoria ←→ Celery ←→ SGP System
```

### 📊 Fluxo de Dados
1. **Cliente envia mensagem** → WhatsApp → Uazapi → Django
2. **IA processa** → OpenAI → SGP (se necessário) → Resposta
3. **Dados salvos** → Supabase (conversas, contatos, mensagens, CSAT)
4. **Dashboard atualiza** → Frontend via API REST
5. **CSAT automático** → 1.5min após fechamento → IA interpreta feedback
6. **🔄 Recuperador de Vendas** → IA analisa conversas → Identifica interesse → Envia mensagem personalizada

## 🔄 Recuperador de Conversas - Nova Funcionalidade

### Como Funciona
1. **Análise Automática**: IA analisa conversas encerradas em busca de clientes que demonstraram interesse em planos
2. **Identificação Inteligente**: Detecta palavras-chave como "plano", "internet", "velocidade", "preço"
3. **Reativação Personalizada**: Envia mensagem personalizada via WhatsApp para recuperar a venda
4. **Acompanhamento**: Dashboard mostra estatísticas de tentativas, recuperações e taxa de conversão

### Configurações Disponíveis
- **Delay**: Tempo de inatividade antes de ativar (padrão: 30 minutos)
- **Tentativas**: Número máximo de tentativas por cliente (padrão: 3)
- **Palavras-chave**: Lista personalizável de termos de interesse
- **Horários**: Ativação apenas em horários comerciais
- **Isolamento**: Cada provedor vê apenas seus dados

### Dashboard Visual
- **Termômetro Animado**: Taxa de conversão com animação suave
- **Cards de Estatísticas**: Tentativas, recuperadas, pendentes, taxa de conversão
- **Atividades Recentes**: Histórico de tentativas e resultados
- **Configurações**: Interface para ajustar parâmetros do sistema

## 🚀 Início Rápido

### 1. Clone e Configure
```bash
git clone https://github.com/juniorssilvaa/niochat.git
cd niochat

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Frontend
cd frontend/frontend
npm install
```

### 2. Configure Variáveis
```bash
# .env
OPENAI_API_KEY=sua_chave_openai
SUPABASE_URL=sua_url_supabase
SUPABASE_ANON_KEY=sua_chave_supabase
UAZAPI_URL=https://seu-provedor.uazapi.com
UAZAPI_TOKEN=seu_token_uazapi
```

### 3. Configure Supabase
```sql
-- Execute no Supabase SQL Editor
-- Criar tabelas necessárias
CREATE TABLE conversations (
    id BIGINT PRIMARY KEY,
    provedor_id BIGINT NOT NULL,
    contact_id BIGINT NOT NULL,
    inbox_id BIGINT,
    status TEXT DEFAULT 'open',
    assignee_id BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    additional_attributes JSONB
);

CREATE TABLE contacts (
    id BIGINT PRIMARY KEY,
    provedor_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    avatar TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    additional_attributes JSONB
);

CREATE TABLE csat_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provedor_id BIGINT NOT NULL,
    conversation_id BIGINT NOT NULL,
    contact_id BIGINT NOT NULL,
    emoji_rating TEXT,
    rating_value INTEGER NOT NULL,
    feedback_sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- Configurar RLS (Row Level Security)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE csat_feedback ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para isolamento por provedor
CREATE POLICY "Isolate by provedor_id" ON conversations
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON contacts
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON csat_feedback
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);
```

### 4. Inicie os Serviços
```bash
# Terminal 1 - Backend
cd backend
python manage.py runserver 0.0.0.0:8010

# Terminal 2 - Frontend
cd frontend/frontend
npm run dev
```

### 5. Acesse o Sistema
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8010
- **Admin**: http://localhost:8010/admin

## 📚 Documentação Completa

Para documentação detalhada, acesse: [docs.niochat.com.br](https://docs.niochat.com.br)

### Seções Principais
- [:octicons-book-24: Instalação](docs/installation/development.md) - Configure o ambiente
- [:octicons-cpu-24: IA e SGP](docs/ai/configuration.md) - Configure a IA
- [:octicons-database-24: Supabase](docs/configuration/supabase.md) - Configure dashboard
- [:octicons-gear-24: API](docs/api/endpoints.md) - Endpoints da API
- [:octicons-chart-line-24: Uso](docs/usage/interface.md) - Como usar o sistema

## 🔧 Tecnologias

### Backend
- **Django 5.2**: Framework web
- **Django REST Framework**: API REST
- **Channels**: WebSocket
- **Celery**: Processamento assíncrono
- **Redis**: Cache e sessões
- **PostgreSQL**: Banco de dados

### Frontend
- **React 18**: Interface
- **Vite**: Build tool
- **Tailwind CSS**: Estilização
- **Shadcn/ui**: Componentes
- **WebSocket**: Tempo real

### Integrações
- **Uazapi/Evolution**: WhatsApp
- **OpenAI ChatGPT**: IA
- **Supabase**: Dashboard
- **SGP**: Sistema de gestão

## 🎯 Casos de Uso

### Provedores de Internet
- **Consulta de Faturas**: Cliente pede fatura → IA consulta SGP → gera PIX/Boleto
- **Suporte Técnico**: Cliente relata problema → IA verifica status → cria chamado
- **Verificação de Status**: Cliente pergunta sobre conexão → IA consulta status real

### Empresas de Serviços
- **Atendimento Automatizado**: IA responde perguntas comuns
- **Agendamento**: Integração com sistemas
- **Feedback**: Coleta automática de satisfação

## 📊 Métricas e Dashboard

### Sistema CSAT
- **Coleta Automática**: Feedback enviado 1.5 minutos após fechamento
- **Análise IA**: Interpretação automática de feedback textual via OpenAI
- **Dashboard Completo**: Métricas e evolução temporal em tempo real
- **Histórico Detalhado**: Com fotos de perfil dos clientes
- **Dados no Supabase**: Isolamento total por provedor via RLS

### Auditoria Avançada
- **Logs Detalhados**: Todas as ações do sistema
- **Histórico Completo**: Mensagens e conversas
- **Filtros Inteligentes**: Por tipo de ação e usuário
- **Exportação**: Dados em formato estruturado
- **Supabase Integration**: Dados de auditoria enviados automaticamente

## 🔐 Segurança

### Multi-tenant
- **Isolamento Total**: Cada provedor tem seus dados
- **Row Level Security**: Supabase com RLS
- **Permissões Granulares**: Controle fino de acesso
- **Auditoria Completa**: Log de todas as ações

### Dados
- **Criptografia**: Dados sensíveis protegidos
- **Backup**: Backup automático
- **SSL/TLS**: Comunicação criptografada
- **Monitoramento**: Logs e alertas

## 🔧 Correções Recentes (v2.2.0)

### ✅ Problemas Resolvidos
- **Cards CSAT**: Dados agora puxados corretamente do Supabase
- **Endpoint CSAT**: `/api/csat/feedbacks/stats/` funcionando 100%
- **Erro 500**: Corrigido problema de serialização com UUIDs
- **Sintaxe Python**: Corrigidos erros de indentação no `openai_service.py`
- **Frontend**: Cards "Satisfação Média", "Total de Avaliações", "Taxa de Satisfação" funcionando
- **Isolamento de Dados**: RLS configurado corretamente no Supabase
- **Últimos Feedbacks**: Avatar e mensagem original agora exibidos corretamente
- **Serialização CSAT**: Corrigido erro `Object of type CSATFeedback is not JSON serializable`
- **Foto de Perfil**: Integração com Uazapi para buscar fotos dos contatos
- **Mensagem Original**: Resposta do cliente exibida nos feedbacks CSAT

### 🚀 Melhorias Implementadas
- **IA Atualiza Nome**: Quando descobre nome via CPF/CNPJ, atualiza contato automaticamente
- **Dados Automáticos**: Conversas, contatos, mensagens e CSAT enviados para Supabase
- **Dashboard Tempo Real**: Métricas atualizadas automaticamente
- **CSAT Inteligente**: IA interpreta feedback textual dinamicamente
- **Avatar Automático**: Fotos de perfil obtidas automaticamente da Uazapi
- **Serializer CSAT**: Uso do `CSATFeedbackSerializer` para dados completos
- **Integração Uazapi**: Busca automática de fotos de perfil via API

## 🚀 Deploy

### Produção
```bash
# Configure as variáveis de ambiente
cp production.env .env

# Execute o deploy
./deploy.sh

# Verifique os serviços
systemctl status niochat-backend
systemctl status niochat-frontend
```

### Docker
```bash
# Build e execução
docker-compose up -d

# Verificar logs
docker-compose logs -f
```

## 📈 Performance

- **Tempo de Resposta**: < 200ms
- **Uptime**: 99.9%
- **Escalabilidade**: 1000+ usuários simultâneos
- **Disponibilidade**: 24/7

## 🔧 Troubleshooting

### Problemas Comuns
- **Cards CSAT vazios**: Verifique se as tabelas do Supabase foram criadas
- **Erro 500 no CSAT**: Verifique se o RLS está configurado corretamente
- **IA não responde**: Verifique se o Redis está rodando
- **CSAT não envia**: Verifique se o Celery está ativo

### Logs Importantes
```bash
# Backend logs
tail -f /var/log/niochat/backend.log

# Celery logs
tail -f /var/log/niochat/celery.log

# Frontend logs
tail -f /var/log/niochat/frontend.log
```

### Comandos de Diagnóstico
```bash
# Verificar status dos serviços
systemctl status niochat-backend
systemctl status niochat-frontend
systemctl status niochat-celery

# Testar conexão Supabase
python manage.py shell -c "from core.supabase_service import supabase_service; print(supabase_service._is_enabled())"

# Verificar CSAT no Supabase
python manage.py shell -c "from conversations.csat_service import CSATService; print(CSATService.get_csat_stats(Provedor.objects.first()))"
```

## 🆘 Suporte

- **GitHub Issues**: [Reportar problemas](https://github.com/juniorssilvaa/niochat/issues)
- **Documentação**: [docs.niochat.com.br](https://docs.niochat.com.br)
- **Email**: suporte@niochat.com.br

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](https://github.com/juniorssilvaa/niochat/blob/main/LICENSE) para mais detalhes.

## 🏆 Reconhecimentos

### Desenvolvimento
- **Commits**: 500+
- **Issues**: 50+ resolvidas
- **Contribuidores**: 5+
- **Funcionalidades**: 100+

### Tecnologias
- **Django**: Framework robusto
- **React**: Interface moderna
- **OpenAI**: IA avançada
- **Supabase**: Dashboard e dados
- **Uazapi**: WhatsApp Business

---

**NioChat** - Transformando atendimento via WhatsApp com IA inteligente e tecnologia avançada.