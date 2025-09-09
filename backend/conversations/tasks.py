"""
Celery tasks para o app conversations
"""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_csat_message(csat_request_id):
    """
    Task Celery para enviar mensagem de CSAT
    """
    try:
        from .models import CSATRequest
        from .csat_automation import CSATAutomationService
        
        csat_request = CSATRequest.objects.get(id=csat_request_id)
        return CSATAutomationService.send_csat_message(csat_request)
    except CSATRequest.DoesNotExist:
        logger.error(f"CSAT request {csat_request_id} não encontrada")
        return False
    except Exception as e:
        logger.error(f"Erro na task send_csat_message: {e}")
        return False

