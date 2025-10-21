# Instalação em Produção

Este guia explica como instalar e configurar o NioChat em um ambiente de produção.

## Pré-requisitos

### Servidor
- **Sistema Operacional**: Ubuntu 20.04+ ou CentOS 8+
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **CPU**: Mínimo 2 cores, recomendado 4 cores+
- **Disco**: Mínimo 50GB, recomendado 100GB+
- **Rede**: Conexão estável com internet

### Software
- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **Nginx**: 1.18+
- **Docker**: 20+ (opcional)

## Instalação do Sistema

### 1. Atualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependências
```bash
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql redis-server nginx git
```

### 3. Configurar PostgreSQL
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE niochat;
CREATE USER niochat WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE niochat TO niochat;
\q
```

### 4. Configurar Redis (Porta 6379)
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configurar porta 6379 e senha
sudo nano /etc/redis/redis.conf
# Adicionar:
# port 6379
# requirepass SUA_SENHA_REDIS
# bind 0.0.0.0

sudo systemctl restart redis-server
```

### 5. Configurar RabbitMQ
```bash
sudo apt install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server

# Configurar usuário e senha
sudo rabbitmqctl add_user niochat ccf9e819f70a54bb790487f2438da6ee
sudo rabbitmqctl set_user_tags niochat administrator
sudo rabbitmqctl set_permissions -p / niochat ".*" ".*" ".*"
```

## Instalação do NioChat

### 1. Clone do Repositório
```bash
cd /opt
sudo git clone https://github.com/juniorssilvaa/niochat.git
sudo chown -R $USER:$USER niochat
cd niochat
```

### 2. Configurar Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar Frontend
```bash
cd frontend/frontend
npm install
npm run build
```

### 4. Configurar Variáveis de Ambiente
```bash
sudo nano /opt/niochat/backend/.env
```

```env
# Django
DEBUG=False
SECRET_KEY=sua_chave_secreta_aqui
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Banco de Dados
DATABASE_URL=postgresql://niochat:senha_segura@localhost:5432/niochat

# Redis (porta 6380)
REDIS_URL=redis://:SUA_SENHA_REDIS@154.38.176.17:6380/0
REDIS_HOST=154.38.176.17
REDIS_PORT=6380
REDIS_PASSWORD=SUA_SENHA_REDIS

# RabbitMQ (para Celery broker)
CELERY_BROKER_URL=amqp://admin:SUA_SENHA_RABBITMQ@154.38.176.17:5672
CELERY_RESULT_BACKEND=redis://:SUA_SENHA_REDIS@154.38.176.17:6380/0
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

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_app

# Webhook
WEBHOOK_SECRET=seu_secret_webhook
```

### 5. Configurar Django
```bash
cd /opt/niochat/backend
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## Configuração do Nginx

### 1. Criar Configuração
```bash
sudo nano /etc/nginx/sites-available/niochat
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # SSL
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # Frontend
    location / {
        root /opt/niochat/frontend/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Webhooks
    location /webhook/ {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Ativar Site
```bash
sudo ln -s /etc/nginx/sites-available/niochat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Configuração do SSL

### 1. Instalar Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Obter Certificado
```bash
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

### 3. Renovação Automática
```bash
sudo crontab -e
```

```cron
0 12 * * * /usr/bin/certbot renew --quiet
```

## Configuração do Systemd

### 1. Serviço Backend
```bash
sudo nano /etc/systemd/system/niochat-backend.service
```

```ini
[Unit]
Description=NioChat Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/niochat/backend
Environment=PATH=/opt/niochat/backend/venv/bin
ExecStart=/opt/niochat/backend/venv/bin/python manage.py runserver 0.0.0.0:8010
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Serviço Celery
```bash
sudo nano /etc/systemd/system/niochat-celery.service
```

```ini
[Unit]
Description=NioChat Celery Worker
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/niochat/backend
Environment=PATH=/opt/niochat/backend/venv/bin
ExecStart=/opt/niochat/backend/venv/bin/celery -A niochat worker -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Serviço Celery Beat
```bash
sudo nano /etc/systemd/system/niochat-celery-beat.service
```

```ini
[Unit]
Description=NioChat Celery Beat
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/niochat/backend
Environment=PATH=/opt/niochat/backend/venv/bin
ExecStart=/opt/niochat/backend/venv/bin/celery -A niochat beat -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Ativar Serviços
```bash
sudo systemctl daemon-reload
sudo systemctl enable niochat-backend
sudo systemctl enable niochat-celery
sudo systemctl enable niochat-celery-beat
sudo systemctl start niochat-backend
sudo systemctl start niochat-celery
sudo systemctl start niochat-celery-beat
```

## Configuração do Firewall

### 1. UFW
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. Verificar Status
```bash
sudo ufw status
```

## Monitoramento

### 1. Logs do Sistema
```bash
sudo journalctl -u niochat-backend -f
sudo journalctl -u niochat-celery -f
sudo journalctl -u niochat-celery-beat -f
```

### 2. Logs do Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Logs da Aplicação
```bash
sudo tail -f /opt/niochat/backend/logs/django.log
sudo tail -f /opt/niochat/backend/logs/celery.log
```

## Backup

### 1. Script de Backup
```bash
sudo nano /opt/niochat/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
DB_NAME="niochat"
DB_USER="niochat"
DB_PASS="senha_segura"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /opt/niochat

# Remover backups antigos (manter 7 dias)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

### 2. Tornar Executável
```bash
sudo chmod +x /opt/niochat/backup.sh
```

### 3. Agendar Backup
```bash
sudo crontab -e
```

```cron
0 2 * * * /opt/niochat/backup.sh
```

## Atualizações

### 1. Script de Atualização
```bash
sudo nano /opt/niochat/update.sh
```

```bash
#!/bin/bash
cd /opt/niochat

# Backup antes da atualização
./backup.sh

# Parar serviços
sudo systemctl stop niochat-backend
sudo systemctl stop niochat-celery
sudo systemctl stop niochat-celery-beat

# Atualizar código
git pull origin main

# Atualizar dependências
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Migrações
python manage.py migrate
python manage.py collectstatic --noinput

# Rebuild frontend
cd ../frontend/frontend
npm install
npm run build

# Reiniciar serviços
sudo systemctl start niochat-backend
sudo systemctl start niochat-celery
sudo systemctl start niochat-celery-beat

echo "Atualização concluída"
```

### 2. Tornar Executável
```bash
sudo chmod +x /opt/niochat/update.sh
```

## Verificação

### 1. Status dos Serviços
```bash
sudo systemctl status niochat-backend
sudo systemctl status niochat-celery
sudo systemctl status niochat-celery-beat
```

### 2. Teste de Conectividade
```bash
curl -I https://seu-dominio.com
curl -I https://seu-dominio.com/api/health/
```

### 3. Teste de WebSocket
```javascript
const ws = new WebSocket('wss://seu-dominio.com/ws/dashboard/');
ws.onopen = () => console.log('WebSocket conectado');
```

## Troubleshooting

### Problemas Comuns

#### 1. Serviço não inicia
```bash
sudo journalctl -u niochat-backend --no-pager
```

#### 2. Erro de permissão
```bash
sudo chown -R www-data:www-data /opt/niochat
```

#### 3. Erro de banco de dados
```bash
sudo -u postgres psql -d niochat -c "SELECT * FROM django_migrations;"
```

#### 4. Erro de Redis
```bash
redis-cli -h 154.38.176.17 -p 6380 -a SUA_SENHA_REDIS ping
```

#### 5. Erro de RabbitMQ
```bash
sudo systemctl status rabbitmq-server
rabbitmqctl status
```

#### 6. Erro de Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Logs Importantes
```bash
# Django
tail -f /opt/niochat/backend/logs/django.log

# Celery
tail -f /opt/niochat/backend/logs/celery.log

# Nginx
tail -f /var/log/nginx/error.log

# Sistema
journalctl -u niochat-backend -f
```

## Próximos Passos

1. [Configuração](configuration/supabase.md) - Configure integrações
2. [Uso](usage/interface.md) - Aprenda a usar o sistema
3. [API](api/endpoints.md) - Explore a API
4. [Troubleshooting](development/troubleshooting.md) - Resolva problemas
