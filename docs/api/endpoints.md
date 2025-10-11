# Endpoints da API

O NioChat oferece uma API REST completa para integração e automação. Esta seção documenta todos os endpoints disponíveis.

## 🔐 Autenticação

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "usuario",
  "password": "senha"
}
```

**Resposta:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@exemplo.com",
    "first_name": "Nome",
    "last_name": "Sobrenome"
  }
}
```

### Logout
```http
POST /api/auth/logout/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 💬 Conversas

### Listar Conversas
```http
GET /api/conversations/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Parâmetros de Query:**
- `status`: open, closed, pending
- `assignee`: ID do agente
- `team`: ID da equipe
- `search`: Busca por texto
- `page`: Número da página
- `page_size`: Tamanho da página

**Resposta:**
```json
{
  "count": 100,
  "next": "http://localhost:8010/api/conversations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "contact": {
        "id": 1,
        "name": "João Silva",
        "phone": "+5511999999999",
        "profile_picture": "https://example.com/photo.jpg"
      },
      "status": "open",
      "assignee": {
        "id": 1,
        "username": "agente1",
        "first_name": "Agente"
      },
      "team": {
        "id": 1,
        "name": "Suporte"
      },
      "last_message": {
        "id": 1,
        "content": "Olá, como posso ajudar?",
        "timestamp": "2024-01-01T10:00:00Z"
      },
      "created_at": "2024-01-01T09:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Detalhes da Conversa
```http
GET /api/conversations/{id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Atribuir Conversa
```http
POST /api/conversations/{id}/assign/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Resposta:**
```json
{
  "success": true,
  "message": "Conversa atribuída para Agente",
  "conversation": {
    "id": 1,
    "assignee": {
      "id": 1,
      "username": "agente1",
      "first_name": "Agente"
    },
    "status": "open"
  }
}
```

### Transferir para Agente
```http
POST /api/conversations/{id}/transfer/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "user_id": 2
}
```

### Transferir para Equipe
```http
POST /api/conversations/{id}/transfer_to_team/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "team_id": 1,
  "team_name": "SUPORTE TÉCNICO"
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Conversa transferida para equipe SUPORTE TÉCNICO",
  "conversation": {
    "id": 1,
    "status": "pending",
    "assignee": null,
    "team": "SUPORTE TÉCNICO"
  }
}
```

## 📨 Mensagens

### Listar Mensagens
```http
GET /api/messages/?conversation={id}
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Enviar Texto
```http
POST /api/messages/send_text/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "conversation_id": 1,
  "content": "Olá, como posso ajudar?"
}
```

### Enviar Mídia
```http
POST /api/messages/send_media/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: multipart/form-data

{
  "conversation_id": 1,
  "file": [arquivo],
  "message_type": "image"
}
```

### Reagir a Mensagem
```http
POST /api/messages/react/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "message_id": 1,
  "reaction": "👍"
}
```

### Deletar Mensagem
```http
POST /api/messages/delete_message/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "message_id": 1
}
```

## 🤖 IA e SGP

### Processar com IA
```http
POST /api/core/atendimento-ia/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "conversation_id": 1,
  "message": "Quero pagar minha fatura"
}
```

**Resposta:**
```json
{
  "response": "Para gerar sua fatura, preciso do seu CPF.",
  "function_calls": [],
  "needs_input": true
}
```

### Function Calls SGP
A IA executa automaticamente as seguintes funções:

#### Consultar Cliente
```json
{
  "name": "consultar_cliente_sgp",
  "parameters": {
    "cpf_cnpj": "123.456.789-00"
  }
}
```

#### Verificar Acesso
```json
{
  "name": "verificar_acesso_sgp",
  "parameters": {
    "contrato": "12345"
  }
}
```

#### Gerar Fatura
```json
{
  "name": "gerar_fatura_completa",
  "parameters": {
    "contrato": "12345"
  }
}
```

#### Criar Chamado Técnico
```json
{
  "name": "criar_chamado_tecnico",
  "parameters": {
    "cpf_cnpj": "123.456.789-00",
    "motivo": "Sem internet",
    "sintomas": "LED vermelho piscando"
  }
}
```

## 📊 Dashboard

### Métricas do Dashboard
```http
GET /api/dashboard/metrics/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Resposta:**
```json
{
  "total_conversations": 100,
  "open_conversations": 25,
  "closed_conversations": 75,
  "average_satisfaction": 4.2,
  "resolution_rate": 0.85,
  "response_time": 120
}
```

### Estatísticas CSAT
```http
GET /api/csat/feedbacks/stats/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Resposta:**
```json
{
  "total_feedbacks": 50,
  "average_rating": 4.2,
  "rating_distribution": {
    "1": 2,
    "2": 3,
    "3": 8,
    "4": 15,
    "5": 22
  },
  "recent_feedbacks": [
    {
      "id": 1,
      "rating": 5,
      "feedback": "Excelente atendimento!",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

## 🔍 Auditoria

### Logs de Auditoria
```http
GET /api/audit-logs/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Parâmetros de Query:**
- `action`: Tipo de ação
- `user_id`: ID do usuário
- `date_from`: Data inicial
- `date_to`: Data final
- `page`: Número da página

**Resposta:**
```json
{
  "count": 1000,
  "next": "http://localhost:8010/api/audit-logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "action": "conversation_created",
      "details": {
        "conversation_id": 1,
        "contact_name": "João Silva"
      },
      "user": {
        "id": 1,
        "username": "agente1"
      },
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ]
}
```

## 🔗 Webhooks

### Webhook Uazapi/Evolution
```http
POST /api/webhooks/evolution-uazapi/
Content-Type: application/json

{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Olá, como posso ajudar?",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  }
}
```

### Webhook Evolution (Legado)
```http
POST /api/webhooks/evolution/
Content-Type: application/json

{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Olá, como posso ajudar?",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  }
}
```

## 🔧 Integrações

### Integração WhatsApp
```http
GET /api/integrations/whatsapp/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Integração Telegram
```http
GET /api/integrations/telegram/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Integração Email
```http
GET /api/integrations/email/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Integração Webchat
```http
GET /api/integrations/webchat/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📱 WebSocket Events

### Conexão
```javascript
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/');

ws.onopen = function(event) {
    console.log('Conectado ao WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Mensagem recebida:', data);
};
```

### Eventos Disponíveis

#### Chat
```javascript
// Nova mensagem
{
  "type": "chat_message",
  "data": {
    "conversation_id": 1,
    "message": {
      "id": 1,
      "content": "Nova mensagem",
      "sender": "customer"
    }
  }
}

// Reação a mensagem
{
  "type": "message_reaction",
  "data": {
    "message_id": 1,
    "reaction": "👍"
  }
}

// Mensagem deletada
{
  "type": "message_deleted",
  "data": {
    "message_id": 1
  }
}
```

#### Dashboard
```javascript
// Métricas atualizadas
{
  "type": "dashboard_metrics",
  "data": {
    "total_conversations": 100,
    "open_conversations": 25,
    "average_satisfaction": 4.2
  }
}

// CSAT atualizado
{
  "type": "csat_update",
  "data": {
    "conversation_id": 1,
    "rating": 5,
    "feedback": "Excelente!"
  }
}

// Log de auditoria
{
  "type": "audit_log",
  "data": {
    "action": "conversation_created",
    "details": {
      "conversation_id": 1
    }
  }
}
```

#### Status do Usuário
```javascript
// Status online/offline
{
  "type": "user_status",
  "data": {
    "user_id": 1,
    "status": "online"
  }
}
```

## 🔐 Autenticação WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...');
```

## 📊 Códigos de Status

### Sucesso
- **200**: OK
- **201**: Criado
- **204**: Sem conteúdo

### Erro do Cliente
- **400**: Requisição inválida
- **401**: Não autorizado
- **403**: Proibido
- **404**: Não encontrado
- **422**: Entidade não processável

### Erro do Servidor
- **500**: Erro interno do servidor
- **502**: Bad Gateway
- **503**: Serviço indisponível

## 🐛 Tratamento de Erros

### Formato de Erro
```json
{
  "error": "ValidationError",
  "message": "Dados inválidos",
  "details": {
    "field": "conversation_id",
    "message": "Este campo é obrigatório"
  }
}
```

### Exemplos de Erro
```json
{
  "error": "AuthenticationError",
  "message": "Token inválido ou expirado"
}
```

```json
{
  "error": "PermissionError",
  "message": "Você não tem permissão para esta ação"
}
```

## 📚 Próximos Passos

1. [:octicons-arrow-right-24: WebSocket](api/websocket.md) - Aprenda sobre WebSocket
2. [:octicons-arrow-right-24: Webhooks](api/webhooks.md) - Aprenda sobre webhooks
3. [:octicons-arrow-right-24: Autenticação](api/authentication.md) - Aprenda sobre autenticação
4. [:octicons-arrow-right-24: Uso](usage/interface.md) - Aprenda a usar a interface

