# Instalação para Desenvolvimento

Este guia irá ajudá-lo a configurar o ambiente de desenvolvimento do NioChat em sua máquina local.

## 📋 Pré-requisitos

### Software Necessário
- **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **Git**: [Download Git](https://git-scm.com/)
- **PostgreSQL 14+** (opcional, SQLite por padrão)
- **Redis**: [Download Redis](https://redis.io/download)

### Verificação dos Pré-requisitos
```bash
# Verificar Python
python --version
# Deve mostrar Python 3.12+

# Verificar Node.js
node --version
# Deve mostrar v18+

# Verificar Git
git --version
# Deve mostrar Git 2.0+

# Verificar Redis
redis-server --version
# Deve mostrar Redis 6.0+
```

## 🚀 Instalação Passo a Passo

### 1. Clone o Repositório
```bash
git clone https://github.com/juniorssilvaa/niochat.git
cd niochat
```

### 2. Configure o Ambiente Python

#### Criar Ambiente Virtual
```bash
python -m venv venv
```

#### Ativar Ambiente Virtual
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configure o Banco de Dados

#### Opção 1: SQLite (Padrão - Mais Simples)
```bash
# Nenhuma configuração adicional necessária
# O Django usará SQLite automaticamente
```

#### Opção 2: PostgreSQL (Recomendado para Produção)
```bash
# Instalar PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE niochat;
CREATE USER niochat_user WITH PASSWORD 'niochat_password';
GRANT ALL PRIVILEGES ON DATABASE niochat TO niochat_user;
\q
```

### 4. Configure as Variáveis de Ambiente

#### Copiar Arquivo de Exemplo
```bash
cp env.example .env
```

#### Editar Arquivo .env
```bash
nano .env
```

#### Configurações Essenciais
```bash
# Django
SECRET_KEY=sua_chave_secreta_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados (SQLite - padrão)
DATABASE_URL=sqlite:///db.sqlite3

# Banco de Dados (PostgreSQL - opcional)
# DATABASE_URL=postgresql://niochat_user:niochat_password@localhost/niochat

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI (para IA)
OPENAI_API_KEY=sua_chave_openai_aqui

# Supabase (para dashboard)
SUPABASE_URL=sua_url_supabase_aqui
SUPABASE_KEY=sua_chave_supabase_aqui

# Uazapi (para WhatsApp)
UAZAPI_URL=https://seu-provedor.uazapi.com
UAZAPI_TOKEN=seu_token_uazapi_aqui
```

### 5. Execute as Migrações
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie um Superusuário
```bash
python manage.py createsuperuser
```

### 7. Configure o Frontend

#### Instalar Dependências
```bash
cd frontend/frontend
npm install
# ou
pnpm install
```

### 8. Inicie os Serviços

#### Terminal 1 - Redis
```bash
redis-server
```

#### Terminal 2 - Backend
```bash
cd backend
python manage.py runserver 0.0.0.0:8010
```

#### Terminal 3 - Frontend
```bash
cd frontend/frontend
npm run dev
```

#### Terminal 4 - Celery (Opcional)
```bash
cd backend
celery -A niochat worker -l info
```

## 🌐 Acessar o Sistema

### URLs de Acesso
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8010
- **Admin**: http://localhost:8010/admin
- **API**: http://localhost:8010/api/

### Primeiro Acesso
1. Acesse http://localhost:8010/admin
2. Faça login com o superusuário criado
3. Configure um provedor
4. Configure as integrações
5. Acesse o frontend em http://localhost:5173

## 🔧 Configurações Adicionais

### Configurar Provedor
1. Acesse o admin Django
2. Vá em **Core > Provedores**
3. Clique em **Adicionar Provedor**
4. Preencha os dados:
   - Nome: Nome da empresa
   - CNPJ: CNPJ da empresa
   - Email: Email de contato
   - Telefone: Telefone de contato

### Configurar Integrações
1. Vá em **Integrations > WhatsApp Integrations**
2. Clique em **Adicionar Integração**
3. Preencha:
   - Provedor: Selecione o provedor
   - Instance Name: Nome da instância
   - Webhook URL: URL do webhook
   - Settings: Configurações JSON

### Configurar IA
1. Vá em **Core > Configurações do Sistema**
2. Configure:
   - Chave API OpenAI
   - Configurações de transcrição
   - Personalidade da IA

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro: "ModuleNotFoundError"
```bash
# Verifique se o ambiente virtual está ativo
which python
# Deve mostrar o caminho do venv

# Reinstale as dependências
pip install -r requirements.txt
```

#### Erro: "Database connection failed"
```bash
# Verifique se o PostgreSQL está rodando
sudo systemctl status postgresql

# Verifique as credenciais no .env
# Teste a conexão
psql -U niochat_user -d niochat -h localhost
```

#### Erro: "Redis connection failed"
```bash
# Verifique se o Redis está rodando
redis-cli ping
# Deve retornar PONG

# Inicie o Redis
redis-server
```

#### Erro: "Port already in use"
```bash
# Verifique qual processo está usando a porta
lsof -i :8010
lsof -i :5173

# Mate o processo
kill -9 PID_DO_PROCESSO
```

#### Frontend não carrega
```bash
# Verifique se o Vite está rodando
cd frontend/frontend
npm run dev

# Verifique os logs
npm run dev -- --verbose
```

#### WebSocket não conecta
```bash
# Verifique se o Redis está rodando
redis-cli ping

# Verifique os logs do Django
tail -f logs/backend.log
```

## 📝 Scripts Úteis

### Script de Inicialização
```bash
#!/bin/bash
# start_dev.sh

# Ativar ambiente virtual
source venv/bin/activate

# Iniciar Redis
redis-server &

# Iniciar Backend
cd backend
python manage.py runserver 0.0.0.0:8010 &

# Iniciar Frontend
cd ../frontend/frontend
npm run dev &

# Iniciar Celery
cd ../../backend
celery -A niochat worker -l info &

wait
```

### Script de Limpeza
```bash
#!/bin/bash
# clean_dev.sh

# Parar todos os processos
pkill -f "python manage.py runserver"
pkill -f "npm run dev"
pkill -f "celery worker"
pkill -f "redis-server"

# Limpar cache
rm -rf frontend/frontend/node_modules/.vite
rm -rf backend/__pycache__
rm -rf backend/*/__pycache__

# Limpar banco (cuidado!)
# python manage.py flush
```

## 🔍 Verificação da Instalação

### Teste Backend
```bash
curl http://localhost:8010/api/
# Deve retornar JSON com informações da API
```

### Teste Frontend
```bash
curl http://localhost:5173
# Deve retornar HTML da aplicação
```

### Teste WebSocket
```bash
# Use um cliente WebSocket para testar
# ws://localhost:8010/ws/dashboard/
```

### Teste Integrações
```bash
# Teste OpenAI
python manage.py shell -c "from core.openai_service import openai_service; print(openai_service.test_connection())"

# Teste Supabase
python manage.py shell -c "from core.supabase_service import supabase_service; print(supabase_service.test_connection())"
```

## 📚 Próximos Passos

1. [:octicons-arrow-right-24: Configuração](configuration/environment.md) - Configure variáveis de ambiente
2. [:octicons-arrow-right-24: Integrações](configuration/integrations.md) - Configure WhatsApp e IA
3. [:octicons-arrow-right-24: Supabase](configuration/supabase.md) - Configure dashboard
4. [:octicons-arrow-right-24: Uso](usage/interface.md) - Aprenda a usar o sistema
