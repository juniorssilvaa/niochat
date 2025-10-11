# Configuração do Supabase

O Supabase é usado para dashboard em tempo real, auditoria avançada e sistema CSAT. Esta seção explica como configurar a integração completa.

## 🎯 Funcionalidades do Supabase

### Dashboard em Tempo Real
- **Métricas Instantâneas**: Taxa de satisfação e resolução em tempo real
- **Atualizações Automáticas**: Via WebSocket do Supabase
- **Filtros Avançados**: Por data, usuário, equipe e provedor

### Sistema de Auditoria
- **Logs Detalhados**: Todas as ações do sistema
- **Histórico Completo**: Mensagens e conversas
- **Filtros Inteligentes**: Por tipo de ação e usuário
- **Exportação**: Dados em formato estruturado

### Sistema CSAT
- **Coleta Automática**: Feedback enviado automaticamente
- **Análise IA**: Interpretação de feedback textual
- **Dashboard Completo**: Métricas e evolução temporal
- **Histórico Detalhado**: Com fotos de perfil dos clientes

## 🚀 Configuração Inicial

### 1. Criar Projeto no Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Crie uma nova conta ou faça login
3. Clique em **"New Project"**
4. Preencha:
   - **Name**: niochat-dashboard
   - **Database Password**: Senha forte
   - **Region**: Escolha a região mais próxima
5. Clique em **"Create new project"**

### 2. Obter Credenciais
1. Vá em **Settings > API**
2. Copie:
   - **Project URL**: `https://seu-projeto.supabase.co`
   - **API Key (anon public)**: Chave pública
   - **API Key (service_role)**: Chave de serviço

### 3. Configurar Variáveis de Ambiente
```bash
# .env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_publica_aqui
SUPABASE_SERVICE_KEY=sua_chave_servico_aqui
```

## 🗄️ Configuração do Banco de Dados

### 1. Criar Tabelas
Execute os scripts SQL no Supabase SQL Editor:

#### Tabela de Mensagens
```sql
-- Tabela de mensagens
CREATE TABLE mensagens (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    provedor_id INTEGER NOT NULL,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    message_type VARCHAR(50),
    sender_type VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_mensagens_conversation_id ON mensagens(conversation_id);
CREATE INDEX idx_mensagens_provedor_id ON mensagens(provedor_id);
CREATE INDEX idx_mensagens_timestamp ON mensagens(timestamp);
```

#### Tabela de Auditoria
```sql
-- Tabela de auditoria
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    provedor_id INTEGER NOT NULL,
    conversation_id INTEGER,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    user_id INTEGER,
    ended_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_auditoria_provedor_id ON auditoria(provedor_id);
CREATE INDEX idx_auditoria_conversation_id ON auditoria(conversation_id);
CREATE INDEX idx_auditoria_ended_at ON auditoria(ended_at);
```

#### Tabela de CSAT
```sql
-- Tabela de CSAT
CREATE TABLE csat_feedback (
    id SERIAL PRIMARY KEY,
    provedor_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    rating_value INTEGER CHECK (rating_value >= 1 AND rating_value <= 5),
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_csat_provedor_id ON csat_feedback(provedor_id);
CREATE INDEX idx_csat_conversation_id ON csat_feedback(conversation_id);
CREATE INDEX idx_csat_created_at ON csat_feedback(created_at);
```

### 2. Configurar Row Level Security (RLS)
```sql
-- Habilitar RLS
ALTER TABLE mensagens ENABLE ROW LEVEL SECURITY;
ALTER TABLE auditoria ENABLE ROW LEVEL SECURITY;
ALTER TABLE csat_feedback ENABLE ROW LEVEL SECURITY;

-- Políticas de segurança
CREATE POLICY "Users can view their own provider data" ON mensagens
    FOR SELECT USING (provedor_id = current_setting('app.current_provedor_id')::integer);

CREATE POLICY "Users can view their own provider data" ON auditoria
    FOR SELECT USING (provedor_id = current_setting('app.current_provedor_id')::integer);

CREATE POLICY "Users can view their own provider data" ON csat_feedback
    FOR SELECT USING (provedor_id = current_setting('app.current_provedor_id')::integer);
```

## 🔧 Configuração do Backend

### 1. Instalar Dependências
```bash
pip install supabase
```

### 2. Configurar Serviço Supabase
O arquivo `backend/core/supabase_service.py` já está configurado:

```python
from supabase import create_client, Client
import os

class SupabaseService:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.supabase: Client = create_client(self.url, self.key)
    
    def save_message(self, provedor_id, conversation_id, message_data):
        # Salva mensagem no Supabase
        pass
    
    def save_audit(self, provedor_id, conversation_id, action, details, user_id, ended_at_iso):
        # Salva log de auditoria no Supabase
        pass
    
    def save_csat(self, provedor_id, conversation_id, rating_value, feedback_text):
        # Salva feedback CSAT no Supabase
        pass
```

### 3. Configurar Integração Automática
O sistema já está configurado para enviar dados automaticamente:

- **Mensagens**: Enviadas quando conversa é encerrada
- **Auditoria**: Enviada instantaneamente
- **CSAT**: Enviado quando feedback é coletado

## 🎨 Configuração do Frontend

### 1. Instalar Dependências
```bash
cd frontend/frontend
npm install @supabase/supabase-js
```

### 2. Configurar Cliente Supabase
O arquivo `frontend/frontend/src/lib/supabase.js` já está configurado:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY

export const supabase = createClient(supabaseUrl, supabaseKey)

// Funções de busca de dados
export const getMessages = async (conversationId, provedorId) => {
  // Busca mensagens do Supabase
}

export const getAuditLogs = async (provedorId, filters = {}) => {
  // Busca logs de auditoria do Supabase
}

export const getAverageSatisfaction = async (provedorId, dateRange) => {
  // Busca satisfação média do Supabase
}

export const getResolutionRate = async (provedorId, dateRange) => {
  // Busca taxa de resolução do Supabase
}
```

### 3. Configurar Variáveis de Ambiente
```bash
# frontend/frontend/.env
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_KEY=sua_chave_publica_aqui
```

## 📊 Dashboard em Tempo Real

### 1. Componentes que Usam Supabase
- **DashboardPrincipal**: Cards de métricas
- **ConversationAudit**: Histórico de conversas
- **CSATDashboard**: Métricas de satisfação

### 2. Atualizações em Tempo Real
```javascript
// Configurar subscrições
const setupRealtimeSubscriptions = () => {
  // CSAT updates
  supabase
    .channel('csat_changes')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'csat_feedback',
      filter: `provedor_id=eq.${provedorId}`
    }, (payload) => {
      // Atualizar dashboard
    })
    .subscribe()

  // Audit updates
  supabase
    .channel('audit_changes')
    .on('postgres_changes', {
      event: '*',
      schema: 'public',
      table: 'auditoria',
      filter: `provedor_id=eq.${provedorId}`
    }, (payload) => {
      // Atualizar auditoria
    })
    .subscribe()
}
```

## 🔍 Verificação da Configuração

### 1. Teste de Conexão
```bash
cd backend
python manage.py shell -c "
from core.supabase_service import supabase_service
print('Testando conexão Supabase...')
result = supabase_service.test_connection()
print(f'Resultado: {result}')
"
```

### 2. Teste de Envio de Dados
```bash
python manage.py shell -c "
from core.supabase_service import supabase_service
print('Testando envio de dados...')
result = supabase_service.save_audit(
    provedor_id=1,
    conversation_id=1,
    action='test',
    details={'test': True},
    user_id=1,
    ended_at_iso='2024-01-01T00:00:00Z'
)
print(f'Resultado: {result}')
"
```

### 3. Verificar no Supabase
1. Acesse o Supabase Dashboard
2. Vá em **Table Editor**
3. Verifique se as tabelas foram criadas
4. Verifique se os dados estão sendo inseridos

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro: "Invalid API key"
```bash
# Verifique as variáveis de ambiente
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Verifique se as chaves estão corretas no Supabase
```

#### Erro: "Row Level Security policy"
```bash
# Verifique se o RLS está configurado corretamente
# Execute as políticas SQL no Supabase
```

#### Dados não aparecem no dashboard
```bash
# Verifique se os dados estão sendo enviados
# Verifique os logs do backend
tail -f logs/backend.log

# Verifique se o provedor_id está correto
```

#### WebSocket não conecta
```bash
# Verifique se o Supabase está configurado para realtime
# Vá em Settings > API > Realtime
# Verifique se está habilitado
```

## 📚 Próximos Passos

1. [:octicons-arrow-right-24: Dashboard](supabase/dashboard.md) - Configure o dashboard
2. [:octicons-arrow-right-24: Auditoria](supabase/audit.md) - Configure a auditoria
3. [:octicons-arrow-right-24: CSAT](supabase/csat.md) - Configure o sistema CSAT
4. [:octicons-arrow-right-24: Uso](usage/dashboard.md) - Aprenda a usar o dashboard
