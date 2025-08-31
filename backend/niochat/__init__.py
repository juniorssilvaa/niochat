"""
Inicialização do projeto Nio Chat
"""

# Importar Celery para garantir que seja carregado quando Django iniciar
from .celery import app as celery_app

__all__ = ('celery_app',)
