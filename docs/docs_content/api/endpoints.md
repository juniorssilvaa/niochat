# Endpoints da API

O NioChat oferece uma API REST completa para integração e automação. Esta seção documenta todos os endpoints disponíveis.

## Autenticação

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
  "token": "afe94c2006465105312e24043b859e5c0628aadf"
}
```

**Nota:** A API retorna apenas o token. Para obter dados do usuário, use `/api/auth/me/` após o login.

### Logout
```http
POST /api/auth/logout/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Informações do Usuário
```http
GET /api/auth/me/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Resposta:**
```json
{
    "id": 3,
    "username": "niochat",
    "email": "contatofinnybot@gmail.com.br",
    "first_name": "Nio",
    "last_name": "chat",
    "provedor_id": 1,
    "user_type": "admin",
    "permissions": [],
    "sound_notifications_enabled": true,
    "new_message_sound": "message_in_02.mp3",
    "new_conversation_sound": "chat_new_08.mp3",
    "session_timeout": 60
}
```

### Timeout de Sessão
```http
POST /api/auth/session-timeout/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "timeout": 60
}
```

**Resposta de Sucesso:**
```json
{
  "message": "Timeout da sessão atualizado com sucesso",
  "session_timeout": 60
}
```

**Resposta de Erro:**
```json
{
  "error": "Timeout da sessão não fornecido"
}
```


## Contatos

### Listar Contatos
```http
GET /api/contacts/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "João Silva",
      "phone": "11999999999",
      "avatar": "https://example.com/avatar1.jpg",
      "inbox": 1,
      "created_at": "2025-10-11T19:55:34.775872-03:00",
      "updated_at": "2025-10-11T20:06:34.300428-03:00",
      "is_online": false,
      "last_seen": null,
      "conversation_count": 1,
      "unread_messages": 0
    },
    {
      "id": 2,
      "name": "Maria Santos",
      "phone": "11988888888",
      "avatar": "https://example.com/avatar2.jpg",
      "inbox": 1,
      "created_at": "2025-10-11T20:04:40.459828-03:00",
      "updated_at": "2025-10-11T20:06:34.300428-03:00",
      "is_online": true,
      "last_seen": "2025-10-11T20:30:00.000000-03:00",
      "conversation_count": 2,
      "unread_messages": 1
    }
  ]
}
```

### Detalhes do Contato
```http
GET /api/contacts/{id}/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

### Criar Contato
```http
POST /api/contacts/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
Content-Type: application/json

{
  "name": "João Silva",
  "phone": "11999999999",
  "email": "joao@exemplo.com",
  "provedor": 1
}
```

**Resposta:**
```json
{
  "id": 14,
  "name": "João Silva",
  "email": "joao@exemplo.com",
  "phone": "11999999999",
  "avatar": null,
  "additional_attributes": {},
  "provedor": 1,
  "created_at": "2025-10-12T00:26:47.361663-03:00",
  "updated_at": "2025-10-12T00:26:47.361663-03:00"
}
```

**Campos Obrigatórios:**
- `name`: Nome do contato
- `phone`: Telefone do contato
- `provedor`: ID do provedor (ex: 1)

**Campos Opcionais:**
- `email`: Email do contato

**Resposta de Sucesso:**
```json
{
  "id": 3,
  "name": "João Silva",
  "phone": "+5511999999999",
  "email": "joao@exemplo.com",
  "avatar": null,
  "inbox": 1,
  "created_at": "2025-10-12T00:21:00.000000-03:00",
  "updated_at": "2025-10-12T00:21:00.000000-03:00",
  "is_online": false,
  "last_seen": null,
  "conversation_count": 0,
  "unread_messages": 0
}
```

## Conversas

### Listar Conversas
```http
GET /api/conversations/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Parâmetros de Query:**
- `search`: Busca por nome ou telefone
- `page`: Número da página
- `page_size`: Tamanho da página

**Resposta:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 12,
      "name": "Minha Vida 😍",
      "email": null,
      "phone": "556392484773",
      "avatar": "https://pps.whatsapp.net/v/t61.24694-24/559942536_2260568477780892_429171894518858519_n.jpg?ccb=11-4&oh=01_Q5Aa2wGmst6l_wRLC1bGQRObsbi7pf4k7e6Svu24z3ZtDcGe7Q&oe=68F2ACE8&_nc_sid=5e03e0&_nc_cat=103",
      "additional_attributes": {
        "event": "messages",
        "chatid": "556392484773@s.whatsapp.net",
        "instance": "11999999999",
        "sender_lid": "249666566365270@lid"
      },
      "provedor": 1,
      "created_at": "2025-10-11T19:55:34.010282-03:00",
      "updated_at": "2025-10-11T19:57:59.568844-03:00",
      "inbox": {
        "id": 1,
        "name": "WhatsApp 11999999999",
        "channel_type": "whatsapp",
        "provedor": 1,
        "is_active": true,
        "created_at": "2025-09-17T23:01:58.067397-03:00"
      }
    },
    {
      "id": 13,
      "name": "Minha Vida ❤️😍",
      "email": null,
      "phone": "559491561248",
      "avatar": "https://pps.whatsapp.net/v/t61.24694-24/564320629_4141239932761672_4017937049576898413_n.jpg?ccb=11-4&oh=01_Q5Aa2wG7KvYDF5uxK2lrwVrQsCcnNxuVJ8w5W_8Ty4F0LxcZRw&oe=68F7DAB1&_nc_sid=5e03e0&_nc_cat=109",
      "additional_attributes": {
        "event": "messages",
        "chatid": "559491561248@s.whatsapp.net",
        "instance": "11999999999",
        "sender_lid": "141880620785739@lid"
      },
      "provedor": 1,
      "created_at": "2025-10-11T20:04:39.896621-03:00",
      "updated_at": "2025-10-11T20:06:31.952866-03:00",
      "inbox": {
        "id": 1,
        "name": "WhatsApp 11999999999",
        "channel_type": "whatsapp",
        "provedor": 1,
        "is_active": true,
        "created_at": "2025-09-17T23:01:58.067397-03:00"
      }
    }
  ]
}
```

### Detalhes do Contato
```http
GET /api/contacts/{id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```


### Atualizar Contato
```http
PUT /api/contacts/{id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "João Silva Atualizado",
  "phone": "+5511999999999"
}
```

## Inboxes

### Listar Inboxes
```http
GET /api/inboxes/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Detalhes da Inbox
```http
GET /api/inboxes/{id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Criar Inbox
```http
POST /api/inboxes/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "WhatsApp Business",
  "channel": 1,
  "provedor": 1
}
```

## Conversas

### Listar Conversas
```http
GET /api/conversations/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 13,
      "contact": {
        "id": 13,
        "name": "Minha Vida ❤️😍",
        "email": null,
        "phone": "559491561248",
        "avatar": "https://pps.whatsapp.net/v/t61.24694-24/564320629_4141239932761672_4017937049576898413_n.jpg?ccb=11-4&oh=01_Q5Aa2wG7KvYDF5uxK2lrwVrQsCcnNxuVJ8w5W_8Ty4F0LxcZRw&oe=68F7DAB1&_nc_sid=5e03e0&_nc_cat=109",
        "additional_attributes": {
          "event": "messages",
          "chatid": "559491561248@s.whatsapp.net",
          "instance": "11999999999",
          "sender_lid": "141880620785739@lid"
        },
        "provedor": 1,
        "created_at": "2025-10-11T20:04:39.896621-03:00",
        "updated_at": "2025-10-11T20:06:31.952866-03:00",
        "inbox": {
          "id": 1,
          "name": "WhatsApp 11999999999",
          "channel_type": "whatsapp",
          "provedor": 1,
          "is_active": true,
          "created_at": "2025-09-17T23:01:58.067397-03:00"
        }
      },
      "inbox": {
        "id": 1,
        "name": "WhatsApp 11999999999",
        "channel_type": "whatsapp",
        "provedor": 1,
        "is_active": true,
        "created_at": "2025-09-17T23:01:58.067397-03:00"
      },
      "assignee": null,
      "status": "snoozed",
      "additional_attributes": {
        "event": "messages",
        "instance": "559484024089"
      },
      "last_message_at": null,
      "created_at": "2025-10-11T20:04:40.407433-03:00",
      "last_message": {
        "id": 240,
        "conversation": 13,
        "message_type": "outgoing",
        "media_type": "outgoing",
        "file_url": null,
        "content": "Atendimento encerrado. Agradecemos o seu contato, senhor Rogério. \n\nTenha uma excelente noite! 😊",
        "is_from_customer": false,
        "created_at": "2025-10-11T20:06:34.300428-03:00",
        "external_id": "559484024089:3EB01FEB66F1A4B05DB145",
        "additional_attributes": {
          "event": "messages",
          "instance": "559484024089"
        }
      }
    }
  ]
}
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
Content-Type: application/json

{
  "user_id": 1
}
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

### Fechar Conversa
```http
POST /api/conversations/{id}/close/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Reabrir Conversa
```http
POST /api/conversations/{id}/reopen/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Estatísticas de Recuperação
```http
GET /api/recovery/stats/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Configurações de Recuperação
```http
POST /api/recovery/settings/{provedor_id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "enabled": true,
  "auto_recovery": true,
  "recovery_interval": 30
}
```

## Mensagens

### Listar Mensagens
```http
GET /api/messages/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "count": 23,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 218,
      "conversation": 12,
      "message_type": "incoming",
      "media_type": "incoming",
      "file_url": null,
      "content": "Ola",
      "is_from_customer": true,
      "created_at": "2025-10-11T19:55:34.775872-03:00",
        "external_id": "11999999999:ABC123DEF456",
      "additional_attributes": {
        "external_id": "559484024089:3EB057A8C58547E3401498"
      }
    },
    {
      "id": 219,
      "conversation": 12,
      "message_type": "outgoing",
      "media_type": "outgoing",
      "file_url": null,
      "content": "Boa noite! Você já é cliente da NIO NET ou deseja conhecer nossos planos?",
      "is_from_customer": false,
      "created_at": "2025-10-11T19:55:38.094792-03:00",
        "external_id": "11999999999:DEF456GHI789",
      "additional_attributes": {}
    }
  ]
}
```

**Parâmetros de Query:**
- `conversation`: ID da conversa
- `page`: Número da página
- `page_size`: Tamanho da página

### Detalhes da Mensagem
```http
GET /api/messages/{id}/
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

### Servir Arquivo de Mídia
```http
GET /api/media/messages/{conversation_id}/{filename}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Equipes

### Listar Equipes
```http
GET /api/teams/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Detalhes da Equipe
```http
GET /api/teams/{id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Criar Equipe
```http
POST /api/teams/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "Suporte Técnico",
  "description": "Equipe de suporte técnico",
  "provedor": 1
}
```

### Membros da Equipe
```http
GET /api/team-members/?team={id}
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Adicionar Membro à Equipe
```http
POST /api/team-members/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "team": 1,
  "user": 2
}
```

## Chat Interno

### Salas de Chat
```http
GET /api/internal-chat/rooms/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Criar Sala de Chat
```http
POST /api/internal-chat/rooms/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "Sala de Suporte",
  "description": "Sala para discussões de suporte"
}
```

### Mensagens do Chat Interno
```http
GET /api/internal-chat/messages/?room={id}
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Enviar Mensagem no Chat Interno
```http
POST /api/internal-chat/messages/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "room": 1,
  "content": "Mensagem interna"
}
```

### Participantes da Sala
```http
GET /api/internal-chat/participants/?room={id}
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Adicionar Participante
```http
POST /api/internal-chat/participants/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "room": 1,
  "user": 2
}
```

### Contagem de Mensagens Não Lidas (Chat Interno)
```http
GET /api/internal-chat-unread-count/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Mensagens Não Lidas por Usuário (Chat Interno)
```http
GET /api/internal-chat-unread-by-user/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Chat Privado

### Mensagens Privadas
```http
GET /api/private-messages/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Enviar Mensagem Privada
```http
POST /api/private-messages/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "recipient": 2,
  "content": "Mensagem privada"
}
```

### Contagem de Mensagens Não Lidas (Chat Privado)
```http
GET /api/private-unread-counts/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## CSAT (Customer Satisfaction)

### Feedbacks CSAT
```http
GET /api/csat/feedbacks/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Estatísticas CSAT
```http
GET /api/csat/feedbacks/stats/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "total_feedbacks": 0,
  "average_rating": 0,
  "satisfaction_rate": 0,
  "rating_distribution": [],
  "channel_distribution": [],
  "daily_stats": [
    {
      "day": "2025-09-12",
      "count": 0,
      "avg_rating": 0
    },
    {
      "day": "2025-09-13",
      "count": 0,
      "avg_rating": 0
    },
    {
      "day": "2025-09-14",
      "count": 0,
      "avg_rating": 0
    }
  ]
}
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
      "contact_name": "João Silva",
      "contact_photo": "https://example.com/photo.jpg",
      "emoji_rating": "🤩",
      "rating_value": 5,
      "original_message": "Excelente atendimento!",
      "feedback_sent_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Solicitações CSAT
```http
GET /api/csat/requests/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Webhook CSAT
```http
POST /api/csat/webhook/
Content-Type: application/json

{
  "conversation_id": 1,
  "rating": 5,
  "feedback": "Excelente atendimento!"
}
```

## Dashboard

### Estatísticas do Dashboard
```http
GET /api/dashboard/stats/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "total_conversas": 2,
  "conversas_abertas": 0,
  "conversas_pendentes": 0,
  "conversas_resolvidas": 1,
  "conversas_em_andamento": 0,
  "contatos_unicos": 2,
  "mensagens_30_dias": 23,
  "tempo_medio_resposta": "0min",
  "tempo_primeira_resposta": "1.2min",
  "taxa_resolucao": "50%",
  "satisfacao_media": "4.4",
  "canais": [
    {
      "inbox__channel_type": "whatsapp",
      "total": 2
    }
  ],
  "atendentes": [
    {
      "name": "amanda",
      "conversations": 0,
      "satisfaction": 4.5
    },
    {
      "name": "Nio chat",
      "conversations": 0,
      "satisfaction": 4.5
    }
  ],
  "atividades": [
    {
      "action": "conversation_closed_agent",
      "user": "niochat",
      "time": "11/10/2025 22:58",
      "type": "activity"
    },
    {
      "action": "conversation_closed_agent",
      "user": "niochat",
      "time": "11/10/2025 22:50",
      "type": "activity"
    }
  ]
}
```

### Estatísticas de Conversas
```http
GET /api/dashboard-stats/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Tempo de Resposta por Hora
```http
GET /api/dashboard/response-time-hourly/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Análise de Conversas
```http
GET /api/analysis/
Authorization: Token afe94c2006465105312e24043b859e5c0628aadf
```

**Resposta:**
```json
{
  "period": "week",
  "date_range": {
    "start": "2025-10-05",
    "end": "2025-10-12"
  },
  "summary": {
    "totalConversations": 2,
    "avgResponseTime": "2.1min",
    "activeAgents": 0,
    "satisfactionRate": "0.0"
  },
  "conversationsByDay": [
    {
      "date": "06/10",
      "conversations": 0
    },
    {
      "date": "07/10",
      "conversations": 0
    },
    {
      "date": "08/10",
      "conversations": 0
    },
    {
      "date": "09/10",
      "conversations": 0
    },
    {
      "date": "10/10",
      "conversations": 0
    },
    {
      "date": "11/10",
      "conversations": 0
    },
    {
      "date": "12/10",
      "conversations": 0
    }
  ],
  "channels": [
    {
      "channel": "whatsapp",
      "conversations": 2
    }
  ]
}
```

### Teste de Análise
```http
GET /api/test-analysis/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## IA e SGP

### Processar com IA
```http
POST /api/atendimento/ia/
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

## Integrações

### WhatsApp
```http
GET /api/integrations/whatsapp/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Telegram
```http
GET /api/integrations/telegram/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Email
```http
GET /api/integrations/email/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Webchat
```http
GET /api/integrations/webchat/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Auditoria

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

## Webhooks

### Webhook Uazapi/Evolution
```http
POST /webhook/evolution-uazapi/
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
POST /webhooks/evolution-uazapi/
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

## Sistema

### Health Check
```http
GET /api/health/
```

### Changelog
```http
GET /api/changelog/
```

### Arquivos Uazapi
```http
GET /api/uazapi/file/{file_id}/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## WebSocket Events

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

### Autenticação WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...');
```

## Códigos de Status

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

## Tratamento de Erros

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

## Guia do Postman

Para facilitar o teste da API, criamos um [Guia Completo do Postman](postman-guide.md) com:
- Configuração passo a passo
- Solução de problemas comuns
- Scripts úteis
- Collection pronta para importar

## Próximos Passos

1. [Autenticação](authentication.md) - Aprenda sobre autenticação
2. [Guia do Postman](postman-guide.md) - Configure o Postman
3. [WebSocket](websocket.md) - Aprenda sobre WebSocket
4. [Webhooks](webhooks.md) - Aprenda sobre webhooks
5. [Uso](../usage/interface.md) - Aprenda a usar a interface