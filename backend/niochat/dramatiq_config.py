"""
Configuração do broker e middleware do Dramatiq
"""
import os
import dramatiq
import pika
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from dramatiq.middleware import AgeLimit, TimeLimit, Callbacks, Pipelines, Prometheus, Retries
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Configurar broker do Dramatiq usando RabbitMQ
logger.info("Configurando RabbitMQ como broker do Dramatiq")

# Configuração do RabbitMQ usando URL e middleware de retentativas
rabbitmq_broker = RabbitmqBroker(
    url="amqp://niochat:ccf9e819f70a54bb790487f2438da6ee@49.12.9.11:5672/",
    middleware=[
        Retries(max_retries=10, min_backoff=30000, max_backoff=900000),
        AgeLimit(),
        TimeLimit(),
        Callbacks(),
        Pipelines(),
        Prometheus()
    ]
)

broker = rabbitmq_broker
logger.info("RabbitMQ configurado com sucesso")

# Configurar backend de resultados com Redis
results_backend = RedisBackend(
    host="49.12.9.11",  # Redis para resultados
    port=6379,
    db=1
)

# Adicionar middleware apenas se não existir
middleware_classes = [type(m) for m in broker.middleware]

if AgeLimit not in middleware_classes:
    broker.add_middleware(AgeLimit(max_age=3600000))  # 1 hora

if TimeLimit not in middleware_classes:
    broker.add_middleware(TimeLimit(time_limit=1800000))  # 30 minutos

if Callbacks not in middleware_classes:
    broker.add_middleware(Callbacks())

if Pipelines not in middleware_classes:
    broker.add_middleware(Pipelines())

if Prometheus not in middleware_classes:
    broker.add_middleware(Prometheus())

if Retries not in middleware_classes:
    broker.add_middleware(Retries(
        max_retries=10,  # Aumentado número máximo de retentativas
        min_backoff=30000,  # Aumentado backoff mínimo para 30 segundos
        max_backoff=900000,  # Aumentado backoff máximo para 15 minutos
        retry_when=lambda *args: True,  # Tentar novamente para qualquer exceção
        jitter=True  # Adiciona variação aleatória no tempo de espera
    ))

if Results not in middleware_classes:
    broker.add_middleware(Results(backend=results_backend))

# Definir broker global
dramatiq.set_broker(broker)