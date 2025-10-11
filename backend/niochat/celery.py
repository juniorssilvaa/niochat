"""
Configuração do Celery para o projeto Nio Chat
"""

import os
from celery import Celery
from django.conf import settings

# Define o módulo de configurações padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')

# Cria a instância principal do Celery
app = Celery('niochat')

# Carrega as configurações do Django com o namespace CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Atualizações e boas práticas de configuração do Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=False,

    # Monitoramento e controle
    task_track_started=True,
    task_time_limit=30 * 60,        # 30 minutos (limite máximo)
    task_soft_time_limit=25 * 60,   # 25 minutos (aviso prévio)

    # Performance e estabilidade do worker
    worker_prefetch_multiplier=1,   # processa uma tarefa por vez (evita bloqueios)
    worker_max_tasks_per_child=1000,# reinicia processos periodicamente
    broker_connection_retry_on_startup=True,  # garante reconexão se Redis estiver lento

    # Scheduler (agendador) usando django_celery_beat
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    beat_schedule={},  # o schedule será gerenciado pelo painel do Django
)

# Descobre automaticamente tasks registradas nos apps instalados
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    """Tarefa de debug padrão"""
    print(f'Request: {self.request!r}')
