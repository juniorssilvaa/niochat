# Webhooks

O NioChat utiliza webhooks para receber notificações em tempo real de eventos do WhatsApp. Este documento explica como implementar e usar webhooks.

## Webhook Uazapi/Evolution

### URL do Webhook
```
POST /webhook/evolution-uazapi/
POST /webhooks/evolution-uazapi/
```

### Estrutura da Requisição
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Olá, como posso ajudar?",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "text"
    }
  }
}
```

### Eventos Suportados

#### Mensagem de Texto
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Olá, como posso ajudar?",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "text",
      "sender": {
        "name": "João Silva",
        "phone": "+5511999999999"
      }
    }
  }
}
```

#### Mensagem de Imagem
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Imagem enviada",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "image",
      "media": {
        "url": "https://example.com/image.jpg",
        "filename": "image.jpg",
        "size": 1024
      },
      "sender": {
        "name": "João Silva",
        "phone": "+5511999999999"
      }
    }
  }
}
```

#### Mensagem de Áudio
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Áudio enviado",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "audio",
      "media": {
        "url": "https://example.com/audio.ogg",
        "filename": "audio.ogg",
        "size": 2048,
        "duration": 30
      },
      "sender": {
        "name": "João Silva",
        "phone": "+5511999999999"
      }
    }
  }
}
```

#### Mensagem de Vídeo
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Vídeo enviado",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "video",
      "media": {
        "url": "https://example.com/video.mp4",
        "filename": "video.mp4",
        "size": 5120
      },
      "sender": {
        "name": "João Silva",
        "phone": "+5511999999999"
      }
    }
  }
}
```

#### Mensagem de Documento
```json
{
  "event": "message",
  "data": {
    "message": {
      "id": "message_id",
      "from": "+5511999999999",
      "to": "+5511888888888",
      "content": "Documento enviado",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "document",
      "media": {
        "url": "https://example.com/document.pdf",
        "filename": "document.pdf",
        "size": 10240
      },
      "sender": {
        "name": "João Silva",
        "phone": "+5511999999999"
      }
    }
  }
}
```

#### Reação a Mensagem
```json
{
  "event": "reaction",
  "data": {
    "message_id": "message_id",
    "reaction": "👍",
    "from": "+5511999999999",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### Mensagem Deletada
```json
{
  "event": "message_deleted",
  "data": {
    "message_id": "message_id",
    "from": "+5511999999999",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### Status de Entrega
```json
{
  "event": "delivery_status",
  "data": {
    "message_id": "message_id",
    "status": "delivered",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### Status de Leitura
```json
{
  "event": "read_status",
  "data": {
    "message_id": "message_id",
    "status": "read",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

## Implementação do Webhook

### Python (Django)
```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_evolution_uazapi(request):
    try:
        data = json.loads(request.body)
        event = data.get('event')
        message_data = data.get('data', {}).get('message', {})
        
        logger.info(f"Webhook recebido: {event}")
        
        if event == 'message':
            process_message(message_data)
        elif event == 'reaction':
            process_reaction(data.get('data', {}))
        elif event == 'message_deleted':
            process_message_deleted(data.get('data', {}))
        elif event == 'delivery_status':
            process_delivery_status(data.get('data', {}))
        elif event == 'read_status':
            process_read_status(data.get('data', {}))
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def process_message(message_data):
    """Processa mensagem recebida"""
    message_id = message_data.get('id')
    from_number = message_data.get('from')
    to_number = message_data.get('to')
    content = message_data.get('content')
    message_type = message_data.get('message_type', 'text')
    
    # Processar mensagem
    logger.info(f"Processando mensagem {message_id} de {from_number}")
    
    # Salvar no banco de dados
    # Enviar para IA
    # Atualizar dashboard via WebSocket

def process_reaction(reaction_data):
    """Processa reação a mensagem"""
    message_id = reaction_data.get('message_id')
    reaction = reaction_data.get('reaction')
    
    logger.info(f"Reação {reaction} na mensagem {message_id}")

def process_message_deleted(deleted_data):
    """Processa mensagem deletada"""
    message_id = deleted_data.get('message_id')
    
    logger.info(f"Mensagem {message_id} foi deletada")

def process_delivery_status(status_data):
    """Processa status de entrega"""
    message_id = status_data.get('message_id')
    status = status_data.get('status')
    
    logger.info(f"Status de entrega da mensagem {message_id}: {status}")

def process_read_status(status_data):
    """Processa status de leitura"""
    message_id = status_data.get('message_id')
    status = status_data.get('status')
    
    logger.info(f"Status de leitura da mensagem {message_id}: {status}")
```

### Node.js (Express)
```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhook/evolution-uazapi', (req, res) => {
  try {
    const { event, data } = req.body;
    const message = data?.message;
    
    console.log(`Webhook recebido: ${event}`);
    
    switch (event) {
      case 'message':
        processMessage(message);
        break;
      case 'reaction':
        processReaction(data);
        break;
      case 'message_deleted':
        processMessageDeleted(data);
        break;
      case 'delivery_status':
        processDeliveryStatus(data);
        break;
      case 'read_status':
        processReadStatus(data);
        break;
      default:
        console.log(`Evento desconhecido: ${event}`);
    }
    
    res.json({ status: 'success' });
  } catch (error) {
    console.error('Erro no webhook:', error);
    res.status(500).json({ status: 'error', message: error.message });
  }
});

function processMessage(message) {
  const { id, from, to, content, message_type } = message;
  console.log(`Processando mensagem ${id} de ${from}`);
  
  // Processar mensagem
  // Salvar no banco de dados
  // Enviar para IA
  // Atualizar dashboard via WebSocket
}

function processReaction(data) {
  const { message_id, reaction } = data;
  console.log(`Reação ${reaction} na mensagem ${message_id}`);
}

function processMessageDeleted(data) {
  const { message_id } = data;
  console.log(`Mensagem ${message_id} foi deletada`);
}

function processDeliveryStatus(data) {
  const { message_id, status } = data;
  console.log(`Status de entrega da mensagem ${message_id}: ${status}`);
}

function processReadStatus(data) {
  const { message_id, status } = data;
  console.log(`Status de leitura da mensagem ${message_id}: ${status}`);
}

app.listen(3000, () => {
  console.log('Servidor rodando na porta 3000');
});
```

### PHP
```php
<?php
header('Content-Type: application/json');

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Dados inválidos']);
    exit;
}

$event = $data['event'] ?? '';
$messageData = $data['data']['message'] ?? [];

error_log("Webhook recebido: $event");

switch ($event) {
    case 'message':
        processMessage($messageData);
        break;
    case 'reaction':
        processReaction($data['data']);
        break;
    case 'message_deleted':
        processMessageDeleted($data['data']);
        break;
    case 'delivery_status':
        processDeliveryStatus($data['data']);
        break;
    case 'read_status':
        processReadStatus($data['data']);
        break;
    default:
        error_log("Evento desconhecido: $event");
}

function processMessage($message) {
    $id = $message['id'] ?? '';
    $from = $message['from'] ?? '';
    $content = $message['content'] ?? '';
    $messageType = $message['message_type'] ?? 'text';
    
    error_log("Processando mensagem $id de $from");
    
    // Processar mensagem
    // Salvar no banco de dados
    // Enviar para IA
    // Atualizar dashboard via WebSocket
}

function processReaction($data) {
    $messageId = $data['message_id'] ?? '';
    $reaction = $data['reaction'] ?? '';
    
    error_log("Reação $reaction na mensagem $messageId");
}

function processMessageDeleted($data) {
    $messageId = $data['message_id'] ?? '';
    error_log("Mensagem $messageId foi deletada");
}

function processDeliveryStatus($data) {
    $messageId = $data['message_id'] ?? '';
    $status = $data['status'] ?? '';
    
    error_log("Status de entrega da mensagem $messageId: $status");
}

function processReadStatus($data) {
    $messageId = $data['message_id'] ?? '';
    $status = $data['status'] ?? '';
    
    error_log("Status de leitura da mensagem $messageId: $status");
}

echo json_encode(['status' => 'success']);
?>
```

## Configuração do Webhook

### Uazapi/Evolution
```json
{
  "webhook": {
    "url": "https://seu-dominio.com/webhook/evolution-uazapi/",
    "events": [
      "message",
      "reaction",
      "message_deleted",
      "delivery_status",
      "read_status"
    ],
    "headers": {
      "Authorization": "Bearer seu_token_aqui"
    }
  }
}
```

### Configuração no NioChat
```python
# settings.py
WEBHOOK_SECRET = 'seu_secret_aqui'
WEBHOOK_TIMEOUT = 30
WEBHOOK_RETRY_ATTEMPTS = 3
```

## Validação de Webhook

### Verificação de Assinatura
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verifica a assinatura do webhook"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_evolution_uazapi(request):
    # Verificar assinatura
    signature = request.headers.get('X-Signature')
    if not verify_webhook_signature(request.body, signature, WEBHOOK_SECRET):
        return JsonResponse({'status': 'error', 'message': 'Assinatura inválida'}, status=401)
    
    # Processar webhook
    # ...
```

### Rate Limiting
```python
from django.core.cache import cache
from django.http import JsonResponse

def rate_limit_webhook(request):
    """Aplica rate limiting ao webhook"""
    client_ip = request.META.get('REMOTE_ADDR')
    cache_key = f"webhook_rate_limit_{client_ip}"
    
    # Limite de 100 requisições por minuto
    current_count = cache.get(cache_key, 0)
    if current_count >= 100:
        return JsonResponse({'status': 'error', 'message': 'Rate limit exceeded'}, status=429)
    
    cache.set(cache_key, current_count + 1, 60)  # 60 segundos
    return None
```

## Tratamento de Erros

### Retry Automático
```python
import time
from django.core.cache import cache

def process_webhook_with_retry(data, max_retries=3):
    """Processa webhook com retry automático"""
    for attempt in range(max_retries):
        try:
            # Processar webhook
            process_webhook(data)
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                # Última tentativa falhou
                logger.error(f"Webhook falhou após {max_retries} tentativas: {e}")
                return False
            else:
                # Aguardar antes da próxima tentativa
                time.sleep(2 ** attempt)  # Backoff exponencial
    
    return False
```

### Logging de Erros
```python
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def webhook_evolution_uazapi(request):
    try:
        data = json.loads(request.body)
        logger.info(f"Webhook recebido: {data.get('event')}")
        
        # Processar webhook
        process_webhook(data)
        
        return JsonResponse({'status': 'success'})
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Erro interno'}, status=500)
```

## Monitoramento

### Métricas de Webhook
```python
from django.core.cache import cache
from django.utils import timezone

def track_webhook_metrics(event, status):
    """Rastreia métricas do webhook"""
    timestamp = timezone.now()
    
    # Incrementar contador de eventos
    cache_key = f"webhook_events_{event}_{status}"
    cache.incr(cache_key, 1)
    cache.expire(cache_key, 3600)  # 1 hora
    
    # Log de métricas
    logger.info(f"Webhook metric: {event} - {status} at {timestamp}")

@csrf_exempt
@require_http_methods(["POST"])
def webhook_evolution_uazapi(request):
    try:
        data = json.loads(request.body)
        event = data.get('event')
        
        # Processar webhook
        process_webhook(data)
        
        # Rastrear métricas
        track_webhook_metrics(event, 'success')
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        # Rastrear métricas de erro
        track_webhook_metrics('error', 'failed')
        raise e
```

## Próximos Passos

1. [Endpoints](endpoints.md) - Explore todos os endpoints da API
2. [WebSocket](websocket.md) - Aprenda sobre WebSocket
3. [Autenticação](authentication.md) - Aprenda sobre autenticação
