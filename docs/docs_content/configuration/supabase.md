# Configuração do Supabase

O NioChat utiliza Supabase para dashboard em tempo real, auditoria e sistema CSAT. Este guia explica como configurar a integração.

## Criar Projeto no Supabase

### 1. Acessar Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Faça login ou crie uma conta
3. Clique em "New Project"

### 2. Configurar Projeto
- **Nome**: NioChat
- **Database Password**: Senha segura
- **Region**: Escolha a região mais próxima
- **Pricing Plan**: Free (para desenvolvimento)

### 3. Obter Credenciais
Após criar o projeto, você encontrará:
- **Project URL**: `https://seu-projeto.supabase.co`
- **Anon Key**: Chave pública para autenticação
- **Service Role Key**: Chave privada para operações administrativas

## Configurar Banco de Dados

### 1. Executar SQL no Supabase
Acesse o SQL Editor no Supabase e execute:

```sql
-- Criar tabela de conversas
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

-- Criar tabela de contatos
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

-- Criar tabela de mensagens
CREATE TABLE messages (
    id BIGINT PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    contact_id BIGINT NOT NULL,
    provedor_id BIGINT NOT NULL,
    content TEXT,
    message_type TEXT DEFAULT 'text',
    is_from_customer BOOLEAN DEFAULT true,
    file_url TEXT,
    file_name TEXT,
    file_size BIGINT,
    external_id TEXT,
    additional_attributes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar tabela de feedback CSAT
CREATE TABLE csat_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provedor_id BIGINT NOT NULL,
    conversation_id BIGINT NOT NULL,
    contact_id BIGINT NOT NULL,
    emoji_rating TEXT,
    rating_value INTEGER NOT NULL,
    original_message TEXT,
    contact_avatar TEXT,
    feedback_sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- Criar tabela de auditoria
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provedor_id BIGINT NOT NULL,
    user_id BIGINT,
    action TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Configurar RLS (Row Level Security)

```sql
-- Habilitar RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE csat_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para isolamento por provedor
CREATE POLICY "Isolate by provedor_id" ON conversations
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON contacts
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON messages
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON csat_feedback
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

CREATE POLICY "Isolate by provedor_id" ON audit_logs
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);
```

### 3. Criar Índices para Performance

```sql
-- Índices para conversas
CREATE INDEX idx_conversations_provedor_id ON conversations(provedor_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_assignee_id ON conversations(assignee_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- Índices para contatos
CREATE INDEX idx_contacts_provedor_id ON contacts(provedor_id);
CREATE INDEX idx_contacts_phone ON contacts(phone);

-- Índices para mensagens
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_provedor_id ON messages(provedor_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Índices para CSAT
CREATE INDEX idx_csat_provedor_id ON csat_feedback(provedor_id);
CREATE INDEX idx_csat_rating_value ON csat_feedback(rating_value);
CREATE INDEX idx_csat_feedback_sent_at ON csat_feedback(feedback_sent_at);

-- Índices para auditoria
CREATE INDEX idx_audit_provedor_id ON audit_logs(provedor_id);
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
```

## Configurar Variáveis de Ambiente

### 1. Arquivo .env
```env
# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anon_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_aqui
```

### 2. Configuração no Django
```python
# settings.py
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
```

## Configurar Dashboard

### 1. Criar Views no Supabase
```sql
-- View para métricas de conversas
CREATE VIEW conversation_metrics AS
SELECT 
    provedor_id,
    COUNT(*) as total_conversations,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_conversations,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_conversations,
    AVG(CASE WHEN status = 'closed' THEN 
        EXTRACT(EPOCH FROM (ended_at - created_at))/3600 
    END) as avg_resolution_time_hours
FROM conversations
GROUP BY provedor_id;

-- View para métricas CSAT
CREATE VIEW csat_metrics AS
SELECT 
    provedor_id,
    COUNT(*) as total_feedbacks,
    AVG(rating_value) as average_rating,
    COUNT(CASE WHEN rating_value = 5 THEN 1 END) as excellent_count,
    COUNT(CASE WHEN rating_value >= 4 THEN 1 END) as satisfied_count,
    COUNT(CASE WHEN rating_value <= 2 THEN 1 END) as unsatisfied_count
FROM csat_feedback
GROUP BY provedor_id;
```

### 2. Configurar Real-time
```sql
-- Habilitar real-time para tabelas
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE csat_feedback;
ALTER PUBLICATION supabase_realtime ADD TABLE audit_logs;
```

## Configurar Autenticação

### 1. Configurar JWT
```python
# settings.py
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')

# Middleware para JWT
MIDDLEWARE = [
    'core.middleware.SupabaseJWTMiddleware',
    # ... outros middlewares
]
```

### 2. Middleware JWT
```python
# core/middleware.py
import jwt
from django.conf import settings

class SupabaseJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Processar JWT do Supabase
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(
                    token, 
                    settings.SUPABASE_JWT_SECRET, 
                    algorithms=['HS256']
                )
                request.supabase_user = payload
            except jwt.InvalidTokenError:
                pass
        
        response = self.get_response(request)
        return response
```

## Configurar Webhooks

### 1. Webhook para Atualizações
```python
# core/supabase_service.py
import requests
from django.conf import settings

class SupabaseService:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.headers = {
            'apikey': settings.SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {settings.SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
    
    def send_webhook(self, event_type, data):
        """Enviar webhook para atualizar dashboard"""
        webhook_url = f"{self.url}/functions/v1/dashboard-update"
        
        payload = {
            'event': event_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=self.headers
        )
        
        return response.status_code == 200
```

### 2. Função Edge para Webhook
```typescript
// supabase/functions/dashboard-update/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { event, data, timestamp } = await req.json()
  
  // Processar evento
  switch (event) {
    case 'conversation_created':
      // Atualizar dashboard
      break
    case 'message_sent':
      // Atualizar chat
      break
    case 'csat_received':
      // Atualizar métricas CSAT
      break
  }
  
  return new Response(JSON.stringify({ success: true }), {
    headers: { "Content-Type": "application/json" },
  })
})
```

## Monitoramento

### 1. Configurar Alertas
```sql
-- Função para alertas
CREATE OR REPLACE FUNCTION check_conversation_alerts()
RETURNS TRIGGER AS $$
BEGIN
    -- Alertar se conversa aberta há mais de 1 hora
    IF NEW.status = 'open' AND 
       EXTRACT(EPOCH FROM (NOW() - NEW.created_at))/3600 > 1 THEN
        -- Enviar notificação
        PERFORM pg_notify('conversation_alert', 
            json_build_object(
                'conversation_id', NEW.id,
                'provedor_id', NEW.provedor_id,
                'alert_type', 'long_open_conversation'
            )::text
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para alertas
CREATE TRIGGER conversation_alert_trigger
    AFTER UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION check_conversation_alerts();
```

### 2. Métricas de Performance
```sql
-- View para performance
CREATE VIEW performance_metrics AS
SELECT 
    provedor_id,
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as conversations_per_hour,
    AVG(EXTRACT(EPOCH FROM (ended_at - created_at))/60) as avg_resolution_minutes,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as resolved_conversations
FROM conversations
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY provedor_id, DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;
```

## Troubleshooting

### Problemas Comuns

#### Erro de Conexão
```bash
# Verificar URL
curl -I https://seu-projeto.supabase.co

# Verificar chave
curl -H "apikey: sua_chave" https://seu-projeto.supabase.co/rest/v1/
```

#### Erro de RLS
```sql
-- Verificar políticas
SELECT * FROM pg_policies WHERE tablename = 'conversations';

-- Testar acesso
SELECT * FROM conversations WHERE provedor_id = 1;
```

#### Erro de Real-time
```sql
-- Verificar publicação
SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';

-- Habilitar tabela
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
```

### Comandos Úteis

#### Verificar Status
```python
# Testar conexão
from core.supabase_service import SupabaseService
supabase = SupabaseService()
print(supabase.test_connection())
```

#### Limpar Dados
```sql
-- Limpar dados de teste
DELETE FROM audit_logs WHERE provedor_id = 999;
DELETE FROM csat_feedback WHERE provedor_id = 999;
DELETE FROM messages WHERE provedor_id = 999;
DELETE FROM conversations WHERE provedor_id = 999;
DELETE FROM contacts WHERE provedor_id = 999;
```

## Próximos Passos

1. [Uso](usage/interface.md) - Aprenda a usar o sistema
2. [API](api/endpoints.md) - Explore a API
3. [Troubleshooting](development/troubleshooting.md) - Resolva problemas