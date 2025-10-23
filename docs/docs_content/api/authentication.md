# Autenticação

O NioChat utiliza autenticação baseada em tokens para proteger a API. Este documento explica como implementar a autenticação em suas integrações.

## Métodos de Autenticação

### Token Authentication
O sistema utiliza Django REST Framework Token Authentication como método principal.

### Headers de Autenticação
```http
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Login

### Endpoint de Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

### Resposta de Sucesso
```json
{
  "token": "afe94c2006465105312e24043b859e5c0628aadf"
}
```

**Nota:** A API retorna apenas o token de autenticação. Para obter informações do usuário, use o endpoint `/api/auth/me/` após o login.

### Resposta de Erro
```json
{
  "error": "InvalidCredentials",
  "message": "Credenciais inválidas"
}
```

## Informações do Usuário

### Obter Dados do Usuário
```http
GET /api/auth/me/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Resposta
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

### Campos da Resposta

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | integer | ID único do usuário |
| `username` | string | Nome de usuário |
| `email` | string | Email do usuário |
| `first_name` | string | Primeiro nome |
| `last_name` | string | Sobrenome |
| `provedor_id` | integer | ID do provedor |
| `user_type` | string | Tipo do usuário (admin, agent, viewer) |
| `permissions` | array | Lista de permissões do usuário |
| `sound_notifications_enabled` | boolean | Notificações sonoras habilitadas |
| `new_message_sound` | string | Som para nova mensagem |
| `new_conversation_sound` | string | Som para nova conversa |
| `session_timeout` | integer | Timeout da sessão em minutos |

## Logout

### Endpoint de Logout
```http
POST /api/auth/logout/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Resposta
```json
{
  "message": "Logout realizado com sucesso"
}
```

## Timeout de Sessão

### Verificar Timeout
```http
POST /api/auth/session-timeout/
Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "timeout": 60
}
```

### Resposta de Sucesso
```json
{
  "message": "Timeout da sessão atualizado com sucesso",
  "session_timeout": 60
}
```

### Resposta de Erro
```json
{
  "error": "Timeout da sessão não fornecido"
}
```

## Implementação em JavaScript

### Exemplo com Fetch
```javascript
class NioChatAPI {
  constructor(baseURL, token = null) {
    this.baseURL = baseURL;
    this.token = token;
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/api/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      this.token = data.token;
      console.log('Token recebido:', data.token);
      return data;
    } else {
      throw new Error('Falha na autenticação');
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (response.status === 401) {
      // Token expirado ou inválido
      this.token = null;
      throw new Error('Sessão expirada');
    }

    return response;
  }

  async get(endpoint) {
    const response = await this.request(endpoint, { method: 'GET' });
    return response.json();
  }

  async post(endpoint, data) {
    const response = await this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async put(endpoint, data) {
    const response = await this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async delete(endpoint) {
    const response = await this.request(endpoint, { method: 'DELETE' });
    return response.json();
  }
}

// Uso
const api = new NioChatAPI('http://localhost:8010');

// Login
try {
  const auth = await api.login('usuario', 'senha');
  console.log('Token:', auth.token);
  
  // Obter dados do usuário após login
  const userInfo = await api.get('/api/auth/me/');
  console.log('Dados do usuário:', userInfo);
} catch (error) {
  console.error('Erro no login:', error);
}

// Fazer requisições autenticadas
try {
  const conversations = await api.get('/api/conversations/');
  console.log('Conversas:', conversations);
} catch (error) {
  console.error('Erro na requisição:', error);
}
```

### Exemplo com Axios
```javascript
import axios from 'axios';

class NioChatAPI {
  constructor(baseURL) {
    this.api = axios.create({
      baseURL: baseURL,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Interceptor para adicionar token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('niochat_token');
      if (token) {
        config.headers.Authorization = `Token ${token}`;
      }
      return config;
    });

    // Interceptor para tratar erros de autenticação
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('niochat_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async login(username, password) {
    try {
      const response = await this.api.post('/api/auth/login/', {
        username,
        password
      });
      
      const { token } = response.data;
      localStorage.setItem('niochat_token', token);
      
      return response.data;
    } catch (error) {
      throw new Error('Falha na autenticação');
    }
  }

  async logout() {
    try {
      await this.api.post('/api/auth/logout/');
      localStorage.removeItem('niochat_token');
    } catch (error) {
      console.error('Erro no logout:', error);
    }
  }

  async getMe() {
    const response = await this.api.get('/api/auth/me/');
    return response.data;
  }
}

// Uso
const api = new NioChatAPI('http://localhost:8010');

// Login
api.login('usuario', 'senha')
  .then(auth => console.log('Autenticado:', auth))
  .catch(error => console.error('Erro:', error));

// Obter dados do usuário
api.getMe()
  .then(user => console.log('Usuário:', user))
  .catch(error => console.error('Erro:', error));
```

## Implementação em Python

### Exemplo com Requests
```python
import requests
from typing import Optional, Dict, Any

class NioChatAPI:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                'Authorization': f'Token {token}'
            })

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Realiza login e obtém token"""
        response = self.session.post(
            f'{self.base_url}/api/auth/login/',
            json={'username': username, 'password': password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            self.session.headers.update({
                'Authorization': f'Token {self.token}'
            })
            return data
        else:
            raise Exception('Falha na autenticação')

    def get(self, endpoint: str) -> Dict[str, Any]:
        """Faz requisição GET"""
        response = self.session.get(f'{self.base_url}{endpoint}')
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Faz requisição POST"""
        response = self.session.post(
            f'{self.base_url}{endpoint}',
            json=data
        )
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Faz requisição PUT"""
        response = self.session.put(
            f'{self.base_url}{endpoint}',
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Faz requisição DELETE"""
        response = self.session.delete(f'{self.base_url}{endpoint}')
        response.raise_for_status()
        return response.json()

    def get_me(self) -> Dict[str, Any]:
        """Obtém dados do usuário atual"""
        return self.get('/api/auth/me/')

    def logout(self) -> None:
        """Realiza logout"""
        self.session.post(f'{self.base_url}/api/auth/logout/')
        self.token = None
        self.session.headers.pop('Authorization', None)

# Uso
api = NioChatAPI('http://localhost:8010')

# Login
try:
    auth = api.login('usuario', 'senha')
    print(f'Token: {auth["token"]}')
except Exception as e:
    print(f'Erro no login: {e}')

# Fazer requisições
try:
    conversations = api.get('/api/conversations/')
    print(f'Conversas: {conversations}')
except Exception as e:
    print(f'Erro na requisição: {e}')
```

## Implementação em PHP

### Exemplo com cURL
```php
<?php
class NioChatAPI {
    private $baseUrl;
    private $token;
    
    public function __construct($baseUrl) {
        $this->baseUrl = $baseUrl;
    }
    
    public function login($username, $password) {
        $data = json_encode([
            'username' => $username,
            'password' => $password
        ]);
        
        $response = $this->makeRequest('/api/auth/login/', 'POST', $data);
        
        if (isset($response['token'])) {
            $this->token = $response['token'];
            return $response;
        } else {
            throw new Exception('Falha na autenticação');
        }
    }
    
    public function get($endpoint) {
        return $this->makeRequest($endpoint, 'GET');
    }
    
    public function post($endpoint, $data) {
        return $this->makeRequest($endpoint, 'POST', json_encode($data));
    }
    
    public function put($endpoint, $data) {
        return $this->makeRequest($endpoint, 'PUT', json_encode($data));
    }
    
    public function delete($endpoint) {
        return $this->makeRequest($endpoint, 'DELETE');
    }
    
    private function makeRequest($endpoint, $method, $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'Content-Type: application/json'
        ];
        
        if ($this->token) {
            $headers[] = 'Authorization: Token ' . $this->token;
        }
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode >= 400) {
            throw new Exception('Erro HTTP: ' . $httpCode);
        }
        
        return json_decode($response, true);
    }
}

// Uso
$api = new NioChatAPI('http://localhost:8010');

try {
    $auth = $api->login('usuario', 'senha');
    echo "Token: " . $auth['token'] . "\n";
    
    $conversations = $api->get('/api/conversations/');
    echo "Conversas: " . json_encode($conversations) . "\n";
} catch (Exception $e) {
    echo "Erro: " . $e->getMessage() . "\n";
}
?>
```

## Tratamento de Erros

### Códigos de Status HTTP

#### 401 - Não Autorizado
```json
{
  "error": "AuthenticationError",
  "message": "Token inválido ou expirado"
}
```

#### 403 - Proibido
```json
{
  "error": "PermissionError",
  "message": "Você não tem permissão para esta ação"
}
```

#### 400 - Requisição Inválida
```json
{
  "error": "ValidationError",
  "message": "Dados inválidos",
  "details": {
    "username": ["Este campo é obrigatório"],
    "password": ["Este campo é obrigatório"]
  }
}
```

### Implementação de Retry
```javascript
class NioChatAPI {
  async requestWithRetry(endpoint, options = {}, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await this.request(endpoint, options);
        return response;
      } catch (error) {
        if (error.message === 'Sessão expirada' && i < maxRetries - 1) {
          // Tentar fazer login novamente
          await this.refreshToken();
          continue;
        }
        throw error;
      }
    }
  }

  async refreshToken() {
    // Implementar lógica de refresh do token
    // ou redirecionar para login
    this.token = null;
    window.location.href = '/login';
  }
}
```

## Segurança

### Boas Práticas

1. **Nunca armazene tokens em localStorage em produção**
2. **Use HTTPS em produção**
3. **Implemente timeout de sessão**
4. **Valide tokens no servidor**
5. **Use tokens com expiração**

### Exemplo de Armazenamento Seguro
```javascript
class SecureTokenStorage {
  static setToken(token) {
    // Em produção, use httpOnly cookies
    if (process.env.NODE_ENV === 'production') {
      // Implementar com cookies httpOnly
      document.cookie = `niochat_token=${token}; path=/; secure; httpOnly`;
    } else {
      // Em desenvolvimento, use sessionStorage
      sessionStorage.setItem('niochat_token', token);
    }
  }

  static getToken() {
    if (process.env.NODE_ENV === 'production') {
      // Ler de cookies
      const cookies = document.cookie.split(';');
      const tokenCookie = cookies.find(cookie => 
        cookie.trim().startsWith('niochat_token=')
      );
      return tokenCookie ? tokenCookie.split('=')[1] : null;
    } else {
      return sessionStorage.getItem('niochat_token');
    }
  }

  static removeToken() {
    if (process.env.NODE_ENV === 'production') {
      document.cookie = 'niochat_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    } else {
      sessionStorage.removeItem('niochat_token');
    }
  }
}
```

## Próximos Passos

1. [Endpoints](endpoints.md) - Explore todos os endpoints da API
2. [WebSocket](websocket.md) - Aprenda sobre WebSocket
3. [Webhooks](webhooks.md) - Aprenda sobre webhooks
