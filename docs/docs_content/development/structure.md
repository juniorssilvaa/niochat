# Estrutura do Projeto

Este documento explica a estrutura do projeto NioChat e como navegar pelo código.

## Estrutura Geral

```
niochat/
├── backend/                 # Django Backend
│   ├── niochat/           # Configurações Django
│   ├── core/              # Aplicação principal
│   ├── conversations/      # Sistema de conversas
│   ├── integrations/       # Integrações externas
│   └── requirements.txt    # Dependências Python
├── frontend/               # React Frontend
│   └── frontend/           # Aplicação React
│       ├── src/           # Código fonte
│       ├── public/        # Arquivos públicos
│       └── package.json   # Dependências Node.js
├── docs/                   # Documentação
├── nginx/                  # Configurações Nginx
├── systemd/                # Serviços Systemd
└── scripts/                # Scripts utilitários
```

## Backend (Django)

### Estrutura do Backend
```
backend/
├── niochat/                # Configurações Django
│   ├── __init__.py
│   ├── settings.py         # Configurações
│   ├── urls.py            # URLs principais
│   ├── wsgi.py            # WSGI
│   ├── asgi.py            # ASGI
│   └── celery.py          # Configuração Celery
├── core/                   # Aplicação principal
│   ├── models.py          # Modelos principais
│   ├── views.py           # Views principais
│   ├── serializers.py     # Serializers
│   ├── urls.py            # URLs da API
│   ├── openai_service.py  # Serviço OpenAI
│   ├── supabase_service.py # Serviço Supabase
│   ├── sgp_client.py      # Cliente SGP
│   └── uazapi_client.py   # Cliente Uazapi
├── conversations/          # Sistema de conversas
│   ├── models.py          # Modelos de conversa
│   ├── views.py           # Views de conversa
│   ├── serializers.py     # Serializers
│   ├── urls.py            # URLs
│   ├── csat_automation.py # Automação CSAT
│   ├── csat_service.py    # Serviço CSAT
│   ├── tasks.py           # Tarefas Celery
│   └── signals.py         # Signals Django
├── integrations/           # Integrações
│   ├── models.py          # Modelos de integração
│   ├── views.py           # Views de integração
│   ├── urls.py            # URLs
│   └── utils.py           # Utilitários
├── manage.py              # Script de gerenciamento
└── requirements.txt       # Dependências
```

### Aplicações Django

#### 1. Core (Aplicação Principal)
- **Responsabilidade**: Funcionalidades centrais
- **Modelos**: User, Provedor, Canal, Company
- **Views**: Autenticação, dashboard, configurações
- **Serviços**: OpenAI, Supabase, SGP, Uazapi

#### 2. Conversations (Sistema de Conversas)
- **Responsabilidade**: Gerenciamento de conversas
- **Modelos**: Conversation, Message, Contact, Inbox
- **Views**: CRUD de conversas, mensagens
- **Features**: CSAT, transferência, atribuição

#### 3. Integrations (Integrações)
- **Responsabilidade**: Integrações externas
- **Modelos**: Integration, Webhook
- **Views**: Webhooks, configurações
- **Features**: WhatsApp, Telegram, Email

## Frontend (React)

### Estrutura do Frontend
```
frontend/frontend/
├── src/                    # Código fonte
│   ├── components/         # Componentes React
│   │   ├── dashboard/     # Componentes do dashboard
│   │   ├── chat/          # Componentes de chat
│   │   ├── ui/            # Componentes UI
│   │   └── layout/        # Componentes de layout
│   ├── hooks/             # Custom hooks
│   ├── services/          # Serviços API
│   ├── utils/             # Utilitários
│   ├── context/           # Context API
│   ├── types/             # TypeScript types
│   └── App.jsx            # Componente principal
├── public/                 # Arquivos públicos
├── package.json           # Dependências
└── vite.config.js         # Configuração Vite
```

### Componentes Principais

#### 1. Dashboard
- **DashboardPrincipal**: Dashboard principal
- **ConversationAnalysis**: Análise de conversas
- **AgentPerformanceTable**: Performance dos agentes
- **CSATDashboard**: Dashboard CSAT

#### 2. Chat
- **ConversationList**: Lista de conversas
- **ChatInterface**: Interface de chat
- **MessageList**: Lista de mensagens
- **MessageInput**: Input de mensagem

#### 3. UI
- **Button**: Botão reutilizável
- **Modal**: Modal reutilizável
- **Table**: Tabela reutilizável
- **Form**: Formulário reutilizável

## Configurações

### 1. Django Settings
```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'core',
    'conversations',
    'integrations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 2. URLs Principais
```python
# niochat/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('conversations.urls')),
    path('api/', include('integrations.urls')),
    path('webhook/evolution-uazapi/', webhook_evolution_uazapi),
]
```

### 3. Configuração Celery
```python
# niochat/celery.py
from celery import Celery
from django.conf import settings

app = Celery('niochat')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## Modelos de Dados

### 1. Core Models
```python
# core/models.py
class Provedor(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class User(AbstractUser):
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE)
    is_agent = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
```

### 2. Conversation Models
```python
# conversations/models.py
class Conversation(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='open')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text')
    is_from_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## APIs e Endpoints

### 1. Core API
```python
# core/urls.py
urlpatterns = [
    path('auth/login/', CustomAuthToken.as_view()),
    path('auth/me/', UserMeView.as_view()),
    path('dashboard/stats/', DashboardStatsView.as_view()),
    path('atendimento/ia/', AtendimentoIAView.as_view()),
]
```

### 2. Conversations API
```python
# conversations/urls.py
urlpatterns = [
    path('conversations/', ConversationViewSet.as_view()),
    path('messages/', MessageViewSet.as_view()),
    path('csat/feedbacks/', CSATFeedbackViewSet.as_view()),
]
```

## Serviços

### 1. OpenAI Service
```python
# core/openai_service.py
class OpenAIService:
    def generate_response(self, message, context):
        # Gerar resposta da IA
        pass
    
    def transcribe_audio(self, audio_file):
        # Transcrever áudio
        pass
    
    def analyze_sentiment(self, text):
        # Analisar sentimento
        pass
```

### 2. Supabase Service
```python
# core/supabase_service.py
class SupabaseService:
    def save_conversation(self, data):
        # Salvar conversa
        pass
    
    def save_message(self, data):
        # Salvar mensagem
        pass
    
    def save_csat(self, data):
        # Salvar CSAT
        pass
```

## Tarefas Celery

### 1. CSAT Automation
```python
# conversations/tasks.py
@shared_task
def send_csat_message(csat_request_id):
    # Enviar mensagem CSAT
    pass

@shared_task
def process_csat_response(message_text, conversation_id):
    # Processar resposta CSAT
    pass
```

### 2. Background Tasks
```python
# conversations/tasks.py
@shared_task
def sync_to_supabase():
    # Sincronizar com Supabase
    pass

@shared_task
def cleanup_old_data():
    # Limpar dados antigos
    pass
```

## WebSocket

### 1. Consumers
```python
# conversations/consumers.py
class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Conectar ao WebSocket
        pass
    
    async def disconnect(self, close_code):
        # Desconectar
        pass
    
    async def receive(self, text_data):
        # Receber mensagem
        pass
```

### 2. Routing
```python
# conversations/routing.py
websocket_urlpatterns = [
    path('ws/dashboard/', DashboardConsumer.as_asgi()),
    path('ws/chat/', ChatConsumer.as_asgi()),
]
```

## Testes

### 1. Testes Unitários
```python
# tests/test_models.py
class ConversationModelTest(TestCase):
    def test_create_conversation(self):
        # Testar criação de conversa
        pass
```

### 2. Testes de Integração
```python
# tests/test_api.py
class ConversationAPITest(APITestCase):
    def test_list_conversations(self):
        # Testar API de conversas
        pass
```

## Deploy

### 1. Docker
```dockerfile
# Dockerfile.backend
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8010"]
```

### 2. Systemd
```ini
# systemd/niochat-backend.service
[Unit]
Description=NioChat Backend
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/niochat/backend
ExecStart=/opt/niochat/backend/venv/bin/python manage.py runserver 0.0.0.0:8010
Restart=always
```

## Próximos Passos

1. [Contribuição](contributing.md) - Como contribuir
2. [Troubleshooting](troubleshooting.md) - Resolver problemas
3. [API](../api/endpoints.md) - Explore a API
4. [Configuração](../configuration/supabase.md) - Configure integrações
