"""
Configuração do Dramatiq para o NioChat
"""
from conversations.tasks import send_csat_message

__all__ = ['send_csat_message']