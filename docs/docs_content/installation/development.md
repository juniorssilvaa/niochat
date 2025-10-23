# Instalação em Desenvolvimento

Este guia explica como configurar o ambiente de desenvolvimento do NioChat.

## Pré-requisitos

### Software Necessário
- **Python**: 3.8 ou superior
- **Node.js**: 16 ou superior
- **PostgreSQL**: 12 ou superior
- **Redis**: 6 ou superior
- **Git**: Para clonar o repositório

### Sistema Operacional
- **Ubuntu**: 20.04+
- **CentOS**: 8+
- **macOS**: 10.15+
- **Windows**: 10+ (com WSL recomendado)

## Instalação

### 1. Clone do Repositório
```bash
git clone https://github.com/juniorssilvaa/niochat.git
cd niochat
```

### 2. Configurar Backend

#### Criar Ambiente Virtual
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

#### Instalar Dependências
```bash
pip install -r requirements.txt
```

#### Configurar Banco de Dados
```bash
# Criar banco de dados
createdb niochat

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

### 3. Configurar Frontend

#### Instalar Dependências
```bash
cd frontend/frontend
npm install
```

#### Build de Desenvolvimento
```bash
npm run build
```

### 4. Configurar Variáveis de Ambiente

#### Criar arquivo .env
```bash
cd backend
cp .env.example .env
```

#### Configurar .env
```env
# Django
DEBUG=True
SECRET_KEY=sua_chave_secreta_aqui
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/niochat

# Redis (porta 6380)
<<<<<<< HEAD
REDIS_URL=redis://:SUA_SENHA_REDIS@	49.12.9.1:6379/0
REDIS_HOST=	49.12.9.1
REDIS_PORT=6379
REDIS_PASSWORD=SUA_SENHA_REDIS

# RabbitMQ (para Celery broker)
CELERY_BROKER_URL=amqp://admin:SUA_SENHA_RABBITMQ@49.12.9.11:5672
CELERY_RESULT_BACKEND=redis://:SUA_SENHA_REDIS@49.12.9.11:6380/0
=======
REDIS_URL=redis://:SUA_SENHA_REDIS@154.38.176.17:6380/0
REDIS_HOST=154.38.176.17
REDIS_PORT=6380
REDIS_PASSWORD=SUA_SENHA_REDIS

# RabbitMQ (para Celery broker)
CELERY_BROKER_URL=amqp://admin:SUA_SENHA_RABBITMQ@154.38.176.17:5672
CELERY_RESULT_BACKEND=redis://:SUA_SENHA_REDIS@154.38.176.17:6380/0
>>>>>>> 3b07e82f46c6cf3f8f20e058d1b016114218f0e0
CELERY_RESULT_EXPIRES=300
CELERY_TASK_IGNORE_RESULT=False

# OpenAI
OPENAI_API_KEY=sua_chave_openai

# Supabase
SUPABASE_URL=sua_url_supabase
SUPABASE_ANON_KEY=sua_chave_supabase

# Uazapi
UAZAPI_URL=https://seu-provedor.uazapi.com
UAZAPI_TOKEN=seu_token_uazapi
```

## Executar o Sistema

### 1. Iniciar Serviços

#### Terminal 1 - Backend
```bash
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8010
```

#### Terminal 2 - Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A niochat worker -l info
```

#### Terminal 3 - Celery Beat
```bash
cd backend
source venv/bin/activate
celery -A niochat beat -l info
```

#### Terminal 4 - Frontend
```bash
cd frontend/frontend
npm run dev
```

### 2. Acessar o Sistema

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8010
- **Admin**: http://localhost:8010/admin

## Configuração Adicional

### Redis (Porta 6380)
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Configurar Redis para porta 6380 (se necessário)
# Editar /etc/redis/redis.conf
# port 6380
# requirepass SUA_SENHA_REDIS
```

### RabbitMQ (para Celery)
```bash
# Ubuntu/Debian
sudo apt install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# CentOS/RHEL
sudo yum install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# macOS
brew install rabbitmq
brew services start rabbitmq

# Configurar usuário e senha
sudo rabbitmqctl add_user admin SUA_SENHA_RABBITMQ
sudo rabbitmqctl set_user_tags admin administrator
sudo rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"
```

### PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb niochat

# CentOS/RHEL
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo -u postgres createdb niochat

# macOS
brew install postgresql
brew services start postgresql
createdb niochat
```

## Desenvolvimento

### Estrutura do Projeto
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
└── docs/                   # Documentação
```

### Comandos Úteis

#### Backend
```bash
# Aplicar migrações
python manage.py migrate

# Criar migração
python manage.py makemigrations

# Shell Django
python manage.py shell

# Testes
python manage.py test

# Coletar estáticos
python manage.py collectstatic
```

#### Frontend
```bash
# Instalar dependências
npm install

# Desenvolvimento
npm run dev

# Build produção
npm run build

# Testes
npm test

# Lint
npm run lint
```

### Debugging

#### Logs do Django
```bash
# Ver logs em tempo real
tail -f logs/django.log

# Configurar nível de log
export DJANGO_LOG_LEVEL=DEBUG
```

#### Logs do Celery
```bash
# Ver logs do worker
tail -f logs/celery.log

# Verificar workers ativos
celery -A niochat inspect active
```

#### Logs do Redis
```bash
# Monitorar Redis
redis-cli monitor

# Verificar conexão
redis-cli ping
```

## Troubleshooting

### Problemas Comuns

#### Porta já em uso
```bash
# Verificar processos na porta
lsof -i :8010
lsof -i :5173

# Matar processo
kill -9 PID
```

#### Erro de banco de dados
```bash
# Verificar conexão
python manage.py dbshell

# Resetar banco
python manage.py flush
```

#### Erro de Redis
```bash
# Verificar status
<<<<<<< HEAD
redis-cli -h 49.12.9.11 -p 6380 -a SUA_SENHA_REDIS ping
=======
redis-cli -h 154.38.176.17 -p 6380 -a SUA_SENHA_REDIS ping
>>>>>>> 3b07e82f46c6cf3f8f20e058d1b016114218f0e0

# Reiniciar Redis
sudo systemctl restart redis-server
```

#### Erro de RabbitMQ
```bash
# Verificar status
sudo systemctl status rabbitmq-server

# Verificar conexão
rabbitmqctl status

# Reiniciar RabbitMQ
sudo systemctl restart rabbitmq-server
```

#### Erro de dependências
```bash
# Atualizar pip
pip install --upgrade pip

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Comandos de Diagnóstico

#### Verificar Status
```bash
# Django
python manage.py check

# Banco de dados
python manage.py dbshell

# Redis
<<<<<<< HEAD
redis-cli -h 49.12.9.11 -p 6380 -a SUA_SENHA_REDIS ping
=======
redis-cli -h 154.38.176.17 -p 6380 -a SUA_SENHA_REDIS ping
>>>>>>> 3b07e82f46c6cf3f8f20e058d1b016114218f0e0

# RabbitMQ
rabbitmqctl status

# Celery
celery -A niochat inspect stats
```

#### Limpar Cache
```bash
# Django
python manage.py clear_cache

# Redis
redis-cli flushall

# Node.js
npm cache clean --force
```

## Próximos Passos

1. [Configuração](configuration/supabase.md) - Configure integrações
2. [Uso](usage/interface.md) - Aprenda a usar o sistema
3. [API](api/endpoints.md) - Explore a API
4. [Troubleshooting](development/troubleshooting.md) - Resolva problemas