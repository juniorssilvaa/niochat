# Configuração Redis e RabbitMQ - NioChat

## Configurações Atuais
O sistema NioChat está configurado para usar:

1. **Redis na porta 6380** - Para cache, WebSockets e resultados do Celery
2. **RabbitMQ na porta 5672** - Para broker do Celery (tasks CSAT)
3. **Configuração otimizada** - Resultados expiram em 5 minutos

## Como Aplicar

### 1. Parar a stack atual
```bash
docker stack rm redis-stack
```

### 2. Aplicar a stack corrigida
```bash
docker stack deploy -c redis-stack-corrected.yml redis-stack
```

### 3. Verificar se está funcionando
```bash
# Verificar se o serviço está rodando
docker service ls | grep redis

# Testar conexão na porta 6380
telnet 154.38.176.17 6380
```

### 4. Configuração do Traefik
Certifique-se de que o Traefik tem as seguintes configurações de entrada:

```yaml
# No traefik.yml ou docker-compose do Traefik
entryPoints:
  redis:
    address: ":6379"
  redis6380:
    address: ":6380"
```

## Configurações Atualizadas no NioChat

As seguintes configurações foram atualizadas para usar a porta 6380:

- `backend/core/redis_memory_service.py`
- `backend/niochat/settings.py`

## Teste de Conexão

Após aplicar a stack, teste a conexão:

```bash
cd /home/junior/niochat/backend
source ../venv/bin/activate
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
import django
django.setup()

from core.redis_memory_service import redis_memory_service

# Testar conexão
redis_conn = redis_memory_service.get_redis_sync()
if redis_conn:
    result = redis_conn.ping()
    print(f'✅ Redis conectado: {result}')
else:
    print('❌ Falha na conexão Redis')
"
```

## Arquivos Criados

- `redis-stack-corrected.yml` - Stack Docker corrigida
- `INSTRUCOES_REDIS.md` - Este arquivo de instruções
