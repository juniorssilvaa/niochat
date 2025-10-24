"""
Configuração inicial do projeto Django
"""
import os
import django
from django.conf import settings

# Configurar Django antes de importar models
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
    django.setup()

# Importar configuração do Dramatiq
from niochat.dramatiq_config import broker
