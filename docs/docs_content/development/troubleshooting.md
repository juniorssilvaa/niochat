# Troubleshooting

Este guia ajuda a resolver problemas comuns no NioChat.

## Problemas de Instalação

### Python não encontrado
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### Node.js não encontrado
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install nodejs
```

### PostgreSQL não encontrado
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Redis não encontrado
```bash
# Ubuntu/Debian
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl enable redis
sudo systemctl start redis
```

## Problemas de Backend

### Erro de migração
```bash
# Verificar status das migrações
python manage.py showmigrations

# Aplicar migrações pendentes
python manage.py migrate

# Resetar migrações (cuidado!)
python manage.py migrate --fake-initial
```

### Erro de banco de dados
```bash
# Verificar conexão
python manage.py dbshell

# Testar conexão
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
```

### Erro de Redis
```bash
# Verificar status
redis-cli ping

# Verificar logs
sudo journalctl -u redis-server
```

### Erro de Celery
```bash
# Verificar status
celery -A niochat inspect active

# Verificar workers
celery -A niochat inspect stats

# Reiniciar worker
sudo systemctl restart niochat-celery
```

## Problemas de Frontend

### Erro de build
```bash
# Limpar cache
npm cache clean --force

# Remover node_modules
rm -rf node_modules package-lock.json

# Reinstalar
npm install

# Build
npm run build
```

### Erro de dependências
```bash
# Verificar versão do Node
node --version

# Atualizar npm
npm install -g npm@latest

# Verificar dependências
npm audit
npm audit fix
```

## Problemas de API

### Erro 500
```bash
# Verificar logs
tail -f logs/django.log

# Verificar settings
python manage.py check

# Verificar banco
python manage.py dbshell
```

### Erro 404
```bash
# Verificar URLs
python manage.py show_urls

# Verificar rotas
python manage.py shell
>>> from django.urls import reverse
>>> reverse('api:conversations-list')
```

### Erro de autenticação
```bash
# Verificar tokens
python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> Token.objects.all()

# Criar token
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from rest_framework.authtoken.models import Token
>>> user = User.objects.get(username='admin')
>>> token = Token.objects.create(user=user)
>>> print(token.key)
```

## Problemas de WebSocket

### Conexão falha
```javascript
// Verificar URL
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/');

// Verificar autenticação
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/?token=seu_token');

// Verificar logs
tail -f logs/django.log
```

### Mensagens não chegam
```bash
# Verificar status do WebSocket
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> channel_layer.send('test', {'type': 'test'})
```

## Problemas de Integração

### Uazapi não conecta
```bash
# Verificar URL
curl -I https://seu-provedor.uazapi.com

# Verificar token
curl -H "Authorization: Bearer seu_token" https://seu-provedor.uazapi.com/api/status
```

### OpenAI não responde
```bash
# Verificar API key
python manage.py shell
>>> from core.openai_service import openai_service
>>> openai_service.test_connection()
```

### Supabase não conecta
```bash
# Verificar configuração
python manage.py shell
>>> from core.supabase_service import supabase_service
>>> supabase_service.test_connection()
```

## Problemas de Performance

### Lento
```bash
# Verificar CPU
top

# Verificar memória
free -h

# Verificar disco
df -h

# Verificar processos
ps aux | grep python
```

### Alto uso de memória
```bash
# Verificar Redis
redis-cli info memory

# Verificar PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Verificar Celery
celery -A niochat inspect stats
```

## Problemas de Logs

### Logs não aparecem
```bash
# Verificar configuração
python manage.py shell
>>> import logging
>>> logger = logging.getLogger('django')
>>> logger.info('Teste')

# Verificar arquivo de log
ls -la logs/
tail -f logs/django.log
```

### Logs muito grandes
```bash
# Rotacionar logs
sudo logrotate -f /etc/logrotate.d/django

# Limpar logs antigos
find logs/ -name "*.log" -mtime +7 -delete
```

## Problemas de Segurança

### Erro de CSRF
```bash
# Verificar configuração
python manage.py shell
>>> from django.conf import settings
>>> settings.CSRF_TRUSTED_ORIGINS
```

### Erro de CORS
```bash
# Verificar configuração
python manage.py shell
>>> from django.conf import settings
>>> settings.CORS_ALLOWED_ORIGINS
```

## Problemas de Deploy

### Build falha
```bash
# Verificar dependências
pip check

# Verificar requirements
pip install -r requirements.txt

# Verificar Python
python --version
```

### Deploy não funciona
```bash
# Verificar permissões
ls -la /opt/niochat/

# Verificar serviços
sudo systemctl status niochat-backend
sudo systemctl status niochat-celery
```

## Comandos Úteis

### Verificar status
```bash
# Serviços
sudo systemctl status niochat-backend
sudo systemctl status niochat-celery
sudo systemctl status niochat-celery-beat

# Banco de dados
sudo -u postgres psql -d niochat -c "SELECT version();"

# Redis
redis-cli ping

# Nginx
sudo nginx -t
```

### Limpar cache
```bash
# Django
python manage.py clear_cache

# Redis
redis-cli flushall

# Nginx
sudo nginx -s reload
```

### Reiniciar serviços
```bash
# Todos os serviços
sudo systemctl restart niochat-backend
sudo systemctl restart niochat-celery
sudo systemctl restart niochat-celery-beat

# Nginx
sudo systemctl restart nginx

# PostgreSQL
sudo systemctl restart postgresql

# Redis
sudo systemctl restart redis-server
```

## Logs Importantes

### Django
```bash
tail -f logs/django.log
```

### Celery
```bash
tail -f logs/celery.log
```

### Nginx
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Sistema
```bash
journalctl -u niochat-backend -f
journalctl -u niochat-celery -f
```

## Contato

Se você não conseguir resolver o problema:

1. **GitHub Issues**: [Reportar problema](https://github.com/juniorssilvaa/niochat/issues)
2. **Email**: suporte@niochat.com.br
3. **Documentação**: Navegue pelas seções da documentação

## Próximos Passos

1. [Instalação](installation/development.md) - Configure o ambiente
2. [Configuração](configuration/supabase.md) - Configure integrações
3. [Uso](usage/interface.md) - Aprenda a usar o sistema
4. [API](api/endpoints.md) - Explore a API
