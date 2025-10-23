# Integração com Supabase

O NioChat utiliza Supabase para dashboard em tempo real, auditoria e sistema CSAT. Este guia explica como implementar e usar a integração.

## Visão Geral

### Funcionalidades
- **Dashboard em Tempo Real**: Métricas atualizadas instantaneamente
- **Auditoria Completa**: Log de todas as ações do sistema
- **Sistema CSAT**: Coleta e análise de satisfação do cliente
- **Isolamento de Dados**: Cada provedor tem seus dados separados
- **Real-time Updates**: Atualizações via WebSocket

### Arquitetura
```
NioChat Backend → Supabase → Dashboard Frontend
     ↓              ↓              ↓
  Django API    PostgreSQL    React App
     ↓              ↓              ↓
  WebSocket    Real-time     WebSocket
```

## Configuração Inicial

### 1. Criar Projeto Supabase
```bash
# Acessar Supabase
https://supabase.com

# Criar novo projeto
- Nome: NioChat
- Database Password: senha_segura
- Region: escolher mais próxima
```

### 2. Obter Credenciais
```env
# Adicionar ao .env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_chave_anon_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_service_role_aqui
```

### 3. Configurar Django
```python
# settings.py
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
```

## Estrutura do Banco

### 1. Tabelas Principais

#### Conversas
```sql
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
```

#### Contatos
```sql
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
```

#### Mensagens
```sql
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
```

#### CSAT Feedback
```sql
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
```

#### Logs de Auditoria
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provedor_id BIGINT NOT NULL,
    user_id BIGINT,
    action TEXT NOT NULL,
    details JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Índices para Performance
```sql
-- Conversas
CREATE INDEX idx_conversations_provedor_id ON conversations(provedor_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_assignee_id ON conversations(assignee_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- Contatos
CREATE INDEX idx_contacts_provedor_id ON contacts(provedor_id);
CREATE INDEX idx_contacts_phone ON contacts(phone);

-- Mensagens
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_provedor_id ON messages(provedor_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- CSAT
CREATE INDEX idx_csat_provedor_id ON csat_feedback(provedor_id);
CREATE INDEX idx_csat_rating_value ON csat_feedback(rating_value);
CREATE INDEX idx_csat_feedback_sent_at ON csat_feedback(feedback_sent_at);

-- Auditoria
CREATE INDEX idx_audit_provedor_id ON audit_logs(provedor_id);
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
```

## Row Level Security (RLS)

### 1. Habilitar RLS
```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE csat_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
```

### 2. Políticas de Isolamento
```sql
-- Política para conversas
CREATE POLICY "Isolate by provedor_id" ON conversations
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

-- Política para contatos
CREATE POLICY "Isolate by provedor_id" ON contacts
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

-- Política para mensagens
CREATE POLICY "Isolate by provedor_id" ON messages
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

-- Política para CSAT
CREATE POLICY "Isolate by provedor_id" ON csat_feedback
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);

-- Política para auditoria
CREATE POLICY "Isolate by provedor_id" ON audit_logs
    FOR ALL USING (provedor_id = current_setting('request.jwt.claims', true)::json->>'provedor_id'::bigint);
```

## Serviço Supabase

### 1. Classe Principal
```python
# core/supabase_service.py
import requests
from django.conf import settings
from typing import Dict, Any, Optional

class SupabaseService:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.headers = {
            'apikey': settings.SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {settings.SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
    
    def _post(self, table: str, data: Dict[str, Any], provedor_id: int) -> bool:
        """Enviar dados para Supabase"""
        try:
            # Adicionar provedor_id para RLS
            data['provedor_id'] = provedor_id
            
            response = requests.post(
                f"{self.url}/rest/v1/{table}",
                json=data,
                headers=self.headers
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Erro ao enviar para Supabase: {e}")
            return False
    
    def save_conversation(self, *, provedor_id: int, conversation_id: int, 
                         contact_id: int, inbox_id: Optional[int] = None,
                         status: str = 'open', assignee_id: Optional[int] = None,
                         additional_attributes: Optional[Dict] = None) -> bool:
        """Salvar conversa no Supabase"""
        payload = {
            "id": conversation_id,
            "contact_id": contact_id,
            "inbox_id": inbox_id,
            "status": status,
            "assignee_id": assignee_id,
            "additional_attributes": additional_attributes or {}
        }
        return self._post("conversations", payload, provedor_id)
    
    def save_contact(self, *, provedor_id: int, contact_id: int, name: str,
                    phone: Optional[str] = None, email: Optional[str] = None,
                    avatar: Optional[str] = None, 
                    additional_attributes: Optional[Dict] = None) -> bool:
        """Salvar contato no Supabase"""
        payload = {
            "id": contact_id,
            "name": name,
            "phone": phone,
            "email": email,
            "avatar": avatar,
            "additional_attributes": additional_attributes or {}
        }
        return self._post("contacts", payload, provedor_id)
    
    def save_message(self, *, provedor_id: int, message_id: int, 
                    conversation_id: int, contact_id: int, content: str,
                    message_type: str = 'text', is_from_customer: bool = True,
                    file_url: Optional[str] = None, file_name: Optional[str] = None,
                    file_size: Optional[int] = None, external_id: Optional[str] = None,
                    additional_attributes: Optional[Dict] = None) -> bool:
        """Salvar mensagem no Supabase"""
        payload = {
            "id": message_id,
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "content": content,
            "message_type": message_type,
            "is_from_customer": is_from_customer,
            "file_url": file_url,
            "file_name": file_name,
            "file_size": file_size,
            "external_id": external_id,
            "additional_attributes": additional_attributes or {}
        }
        return self._post("messages", payload, provedor_id)
    
    def save_csat(self, *, provedor_id: int, conversation_id: int, 
                 contact_id: int, emoji_rating: str, rating_value: int,
                 original_message: Optional[str] = None,
                 contact_avatar: Optional[str] = None,
                 feedback_sent_at_iso: Optional[str] = None) -> bool:
        """Salvar feedback CSAT no Supabase"""
        payload = {
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "emoji_rating": emoji_rating,
            "rating_value": rating_value,
            "original_message": original_message,
            "contact_avatar": contact_avatar,
            "feedback_sent_at": feedback_sent_at_iso
        }
        return self._post("csat_feedback", payload, provedor_id)
    
    def save_audit_log(self, *, provedor_id: int, user_id: Optional[int],
                      action: str, details: Optional[Dict] = None) -> bool:
        """Salvar log de auditoria no Supabase"""
        payload = {
            "user_id": user_id,
            "action": action,
            "details": details or {}
        }
        return self._post("audit_logs", payload, provedor_id)
```

### 2. Uso no Django
```python
# Em views.py
from core.supabase_service import SupabaseService

def create_conversation(request):
    # Criar conversa no Django
    conversation = Conversation.objects.create(...)
    
    # Salvar no Supabase
    supabase_service = SupabaseService()
    supabase_service.save_conversation(
        provedor_id=conversation.provedor.id,
        conversation_id=conversation.id,
        contact_id=conversation.contact.id,
        status=conversation.status
    )
    
    return JsonResponse({'success': True})
```

## Real-time Updates

### 1. Configurar Real-time
```sql
-- Habilitar real-time para tabelas
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
ALTER PUBLICATION supabase_realtime ADD TABLE csat_feedback;
ALTER PUBLICATION supabase_realtime ADD TABLE audit_logs;
```

### 2. Frontend WebSocket
```javascript
// frontend/src/hooks/useSupabase.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY
const supabase = createClient(supabaseUrl, supabaseKey)

export const useSupabaseRealtime = (table, callback) => {
  useEffect(() => {
    const subscription = supabase
      .channel(`${table}_changes`)
      .on('postgres_changes', 
        { event: '*', schema: 'public', table },
        callback
      )
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [table, callback])
}

// Uso
const handleConversationUpdate = (payload) => {
  console.log('Conversa atualizada:', payload)
  // Atualizar estado do React
}

useSupabaseRealtime('conversations', handleConversationUpdate)
```

### 3. Dashboard em Tempo Real
```javascript
// frontend/src/components/Dashboard.jsx
import { useSupabaseRealtime } from '../hooks/useSupabase'

const Dashboard = () => {
  const [metrics, setMetrics] = useState({})
  
  // Atualizar métricas em tempo real
  useSupabaseRealtime('conversations', (payload) => {
    if (payload.eventType === 'INSERT') {
      setMetrics(prev => ({
        ...prev,
        total_conversations: prev.total_conversations + 1
      }))
    }
  })
  
  useSupabaseRealtime('csat_feedback', (payload) => {
    if (payload.eventType === 'INSERT') {
      setMetrics(prev => ({
        ...prev,
        total_feedbacks: prev.total_feedbacks + 1
      }))
    }
  })
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Total de Conversas: {metrics.total_conversations}</p>
      <p>Total de Feedbacks: {metrics.total_feedbacks}</p>
    </div>
  )
}
```

## Sistema CSAT

### 1. Coleta Automática
```python
# conversations/csat_automation.py
from core.supabase_service import SupabaseService

class CSATAutomationService:
    @classmethod
    def process_csat_response(cls, message_text: str, conversation, contact):
        # Processar feedback com IA
        ai_analysis = openai_service.analyze_csat_sentiment(message_text)
        
        # Salvar no Supabase
        supabase_service = SupabaseService()
        supabase_service.save_csat(
            provedor_id=conversation.provedor.id,
            conversation_id=conversation.id,
            contact_id=contact.id,
            emoji_rating=ai_analysis['emoji'],
            rating_value=ai_analysis['rating'],
            original_message=message_text,
            contact_avatar=contact.avatar
        )
        
        return True
```

### 2. Dashboard CSAT
```javascript
// frontend/src/components/CSATDashboard.jsx
import { useSupabaseRealtime } from '../hooks/useSupabase'

const CSATDashboard = () => {
  const [csatData, setCsatData] = useState([])
  
  // Atualizar em tempo real
  useSupabaseRealtime('csat_feedback', (payload) => {
    if (payload.eventType === 'INSERT') {
      setCsatData(prev => [payload.new, ...prev])
    }
  })
  
  return (
    <div>
      <h2>Feedbacks CSAT</h2>
      {csatData.map(feedback => (
        <div key={feedback.id}>
          <p>Rating: {feedback.emoji_rating} ({feedback.rating_value})</p>
          <p>Mensagem: {feedback.original_message}</p>
        </div>
      ))}
    </div>
  )
}
```

## Auditoria

### 1. Log Automático
```python
# core/middleware.py
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log de auditoria
        if request.user.is_authenticated:
            supabase_service = SupabaseService()
            supabase_service.save_audit_log(
                provedor_id=request.user.provedor.id,
                user_id=request.user.id,
                action=f"{request.method} {request.path}",
                details={
                    'ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'status_code': response.status_code
                }
            )
        
        return response
```

### 2. Visualização de Logs
```javascript
// frontend/src/components/AuditLogs.jsx
const AuditLogs = () => {
  const [logs, setLogs] = useState([])
  
  // Atualizar em tempo real
  useSupabaseRealtime('audit_logs', (payload) => {
    if (payload.eventType === 'INSERT') {
      setLogs(prev => [payload.new, ...prev])
    }
  })
  
  return (
    <div>
      <h2>Logs de Auditoria</h2>
      {logs.map(log => (
        <div key={log.id}>
          <p>Ação: {log.action}</p>
          <p>Usuário: {log.user_id}</p>
          <p>Data: {log.timestamp}</p>
        </div>
      ))}
    </div>
  )
}
```

## Monitoramento

### 1. Métricas em Tempo Real
```sql
-- View para métricas
CREATE VIEW dashboard_metrics AS
SELECT 
    provedor_id,
    COUNT(*) as total_conversations,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_conversations,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_conversations,
    AVG(CASE WHEN status = 'closed' THEN 
        EXTRACT(EPOCH FROM (ended_at - created_at))/3600 
    END) as avg_resolution_time_hours
FROM conversations
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY provedor_id;
```

### 2. Alertas Automáticos
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

## Troubleshooting

### 1. Problemas Comuns
```bash
# Verificar conexão
curl -I https://seu-projeto.supabase.co

# Verificar chave
curl -H "apikey: sua_chave" https://seu-projeto.supabase.co/rest/v1/
```

### 2. Logs de Debug
```python
# Testar conexão
from core.supabase_service import SupabaseService
supabase = SupabaseService()
print(supabase.test_connection())
```

### 3. Verificar RLS
```sql
-- Verificar políticas
SELECT * FROM pg_policies WHERE tablename = 'conversations';

-- Testar acesso
SELECT * FROM conversations WHERE provedor_id = 1;
```

## Próximos Passos

1. [Dashboard](supabase/dashboard.md) - Configure o dashboard
2. [CSAT](supabase/csat.md) - Configure o sistema CSAT
3. [Auditoria](supabase/audit.md) - Configure a auditoria
