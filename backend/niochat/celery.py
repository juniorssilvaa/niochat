"""
Configuração do Celery para o projeto Nio Chat
"""

import os
from celery import Celery
from django.conf import settings

# Definir o módulo de configurações padrão do Django para o programa 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')

# Criar instância do Celery
app = Celery('niochat')

# Usar configurações do Django, namespace 'CELERY' significa que todas as
# configurações relacionadas ao Celery devem ter prefixo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configurações adicionais do Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Descobrir automaticamente tasks em todos os apps Django instalados
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
