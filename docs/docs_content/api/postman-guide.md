# Guia de Uso do Postman com NioChat

Este guia explica como configurar e usar o Postman para testar a API do NioChat.

## Configuração Inicial

### 1. Criar Nova Collection
1. Abra o Postman
2. Clique em "New" → "Collection"
3. Nome: "NioChat API"
4. Descrição: "API do NioChat - Sistema de Atendimento WhatsApp"

### 2. Configurar Variáveis de Ambiente
1. Clique em "Environments" → "Create Environment"
2. Nome: "NioChat Local" ou "NioChat Production"
3. Adicione as seguintes variáveis:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8010` | `http://localhost:8010` |
| `token` | (deixar vazio) | (será preenchido após login) |

## Autenticação

### 1. Endpoint de Login
**Método:** `POST`  
**URL:** `{{base_url}}/api/auth/login/`  
**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

**Script de Teste (Tests tab):**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("token", response.token);
    console.log("Token salvo:", response.token);
    console.log("Resposta completa:", response);
} else {
    console.log("Erro no login:", pm.response.text());
}
```

**Resposta Esperada:**
```json
{
  "token": "afe94c2006465105312e24043b859e5c0628aadf"
}
```

### 2. Configurar Authorization Global
1. Vá para a aba "Authorization" da collection
2. Type: "Bearer Token"
3. Token: `{{token}}`

**OU** configure manualmente em cada request:
1. Vá para a aba "Authorization" do request
2. Type: "Custom"
3. Key: `Authorization`
4. Value: `Token {{token}}`

## Endpoints Principais

### 1. Listar Contatos
**Método:** `GET`  
**URL:** `{{base_url}}/api/contacts/`  
**Headers:**
```
Authorization: Token {{token}}
```

**Parâmetros de Query (opcionais):**
- `search`: Busca por nome ou telefone
- `page`: Número da página (padrão: 1)
- `page_size`: Tamanho da página (padrão: 20)

### 2. Informações do Usuário
**Método:** `GET`  
**URL:** `{{base_url}}/api/auth/me/`  
**Headers:**
```
Authorization: Token {{token}}
```

**Resposta Esperada:**
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

### 3. Listar Contatos
**Método:** `GET`  
**URL:** `{{base_url}}/api/contacts/`  
**Headers:**
```
Authorization: Token {{token}}
```

**Resposta Esperada:**
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
      "is_online": false,
      "last_seen": null,
      "conversation_count": 1,
      "unread_messages": 0
    }
  ]
}
```

### 4. Detalhes do Contato
**Método:** `GET`  
**URL:** `{{base_url}}/api/contacts/{id}/`  
**Headers:**
```
Authorization: Token {{token}}
```

### 5. Criar Contato
**Método:** `POST`  
**URL:** `{{base_url}}/api/contacts/`  
**Headers:**
```
Authorization: Token {{token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "name": "João Silva",
  "phone": "11999999999",
  "email": "joao@exemplo.com"
}
```

### 6. Listar Conversas
**Método:** `GET`  
**URL:** `{{base_url}}/api/conversations/`  
**Headers:**
```
Authorization: Token {{token}}
```

### 7. Timeout de Sessão
**Método:** `POST`  
**URL:** `{{base_url}}/api/auth/session-timeout/`  
**Headers:**
```
Authorization: Token {{token}}
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "timeout": 60
}
```

**Resposta Esperada:**
```json
{
  "message": "Timeout da sessão atualizado com sucesso",
  "session_timeout": 60
}
```

### 7. Dashboard Stats
**Método:** `GET`  
**URL:** `{{base_url}}/api/dashboard/stats/`  
**Headers:**
```
Authorization: Token {{token}}
```

### 8. Análise de Conversas
**Método:** `GET`  
**URL:** `{{base_url}}/api/analysis/`  
**Headers:**
```
Authorization: Token {{token}}
```

### 9. Listar Mensagens
**Método:** `GET`  
**URL:** `{{base_url}}/api/messages/`  
**Headers:**
```
Authorization: Token {{token}}
```

### 10. Listar Provedores
**Método:** `GET`  
**URL:** `{{base_url}}/api/provedores/`  
**Headers:**
```
Authorization: Token {{token}}
```

## Solução de Problemas

### Erro 401 - Não Autorizado

#### Problema: "As credenciais de autenticação não foram fornecidas"
**Solução:**
1. Verifique se fez login primeiro
2. Verifique se o token está sendo enviado corretamente
3. Verifique o formato do header Authorization

#### Formato Correto do Header:
```
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**❌ Formato Incorreto:**
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Script para Verificar Token:
```javascript
// Adicione este script na aba "Tests" de cada request
const token = pm.environment.get("token");
if (!token) {
    console.log("❌ Token não encontrado. Faça login primeiro.");
    pm.test("Token exists", () => {
        pm.expect(token).to.not.be.undefined;
    });
} else {
    console.log("✅ Token encontrado:", token.substring(0, 20) + "...");
}
```

### Erro 403 - Proibido
**Solução:**
1. Verifique se o usuário tem permissão para acessar o endpoint
2. Verifique se está logado com o usuário correto
3. Verifique se o provedor está configurado corretamente

### Erro 400 - Requisição Inválida
**Solução:**
1. Verifique se a URL está correta
2. Verifique se o endpoint existe
3. Verifique se o servidor está rodando
4. **Para `/api/auth/session-timeout/`**: Inclua o body JSON com o parâmetro `timeout`

**Exemplo de Body Correto:**
```json
{
  "timeout": 60
}
```

**Erro Comum:**
```json
{
  "error": "Timeout da sessão não fornecido"
}
```

### Erro 404 - Não Encontrado
**Solução:**
1. Verifique se a URL está correta
2. Verifique se o endpoint existe
3. Verifique se o servidor está rodando

### Erro 500 - Erro Interno do Servidor
**Solução:**
1. Verifique os logs do servidor
2. Verifique se o banco de dados está funcionando
3. Verifique se todas as dependências estão instaladas

## Scripts Úteis

### 1. Verificar Status da Resposta
```javascript
pm.test("Status code is 200", () => {
    pm.response.to.have.status(200);
});

pm.test("Response has data", () => {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('data');
});
```

### 2. Salvar ID do Contato
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("contact_id", response.id);
    console.log("ID do contato salvo:", response.id);
}
```

### 3. Verificar Estrutura da Resposta
```javascript
pm.test("Response structure is correct", () => {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('results');
    pm.expect(jsonData).to.have.property('count');
    pm.expect(jsonData).to.have.property('next');
    pm.expect(jsonData).to.have.property('previous');
});
```

### 4. Log de Debug
```javascript
console.log("Request URL:", pm.request.url);
console.log("Request Headers:", pm.request.headers);
console.log("Response Status:", pm.response.status);
console.log("Response Time:", pm.response.responseTime + "ms");
```

## Collection Completa

### Estrutura Recomendada:
```
NioChat API/
├── Authentication/
│   ├── Login
│   ├── Logout
│   └── Get User Info
├── Users/
│   ├── List Users
│   ├── Get User
│   ├── Create User
│   └── Update User
├── Contacts/
│   ├── List Contacts
│   ├── Get Contact
│   ├── Create Contact
│   └── Update Contact
├── Conversations/
│   ├── List Conversations
│   ├── Get Conversation
│   └── Create Conversation
├── Messages/
│   ├── List Messages
│   ├── Send Message
│   └── Get Message
└── Dashboard/
    ├── Get Stats
    ├── Get CSAT Stats
    └── Get Recent Feedbacks
```

## Configuração de Pre-request Scripts

### Para toda a Collection:
```javascript
// Verificar se o token existe
const token = pm.environment.get("token");
if (!token && pm.info.requestName !== "Login") {
    console.log("⚠️ Token não encontrado. Execute o request 'Login' primeiro.");
}
```

### Para requests específicos:
```javascript
// Adicionar timestamp
pm.globals.set("timestamp", new Date().toISOString());
```

## Configuração de Tests

### Para requests de autenticação:
```javascript
pm.test("Login successful", () => {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('token');
    pm.expect(jsonData).to.have.property('user');
});
```

### Para requests de dados:
```javascript
pm.test("Data retrieved successfully", () => {
    pm.response.to.have.status(200);
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.be.an('object');
});
```

## Exportar Collection

1. Clique no menu da collection (três pontos)
2. Selecione "Export"
3. Escolha "Collection v2.1"
4. Salve o arquivo JSON
5. Compartilhe com a equipe

## Importar Collection

1. Clique em "Import"
2. Selecione o arquivo JSON da collection
3. Confirme a importação
4. Configure as variáveis de ambiente

## Próximos Passos

1. [Endpoints](endpoints.md) - Explore todos os endpoints
2. [WebSocket](websocket.md) - Aprenda sobre WebSocket
3. [Webhooks](webhooks.md) - Aprenda sobre webhooks
4. [Troubleshooting](../development/troubleshooting.md) - Resolva problemas
