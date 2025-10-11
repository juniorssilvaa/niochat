import logging
from celery import shared_task
from django.utils import timezone
from conversations.models import CSATRequest
from core.uazapi_client import UazapiClient

logger = logging.getLogger(__name__)


@shared_task
def send_csat_message(csat_request_id: int):
    """
    Tarefa Celery para enviar mensagem de solicitação CSAT
    """
    try:
        csat_request = CSATRequest.objects.get(id=csat_request_id)
        
        if csat_request.status != 'pending':
            logger.info(f"CSAT request {csat_request_id} is not pending, skipping")
            return
        
        # Montar mensagem de feedback
        provedor = csat_request.provedor
        contact = csat_request.contact
        
        # Obter nome do contato
        contact_name = contact.name or "Cliente"
        provedor_name = provedor.nome
        
        csat_message = f"""Olá {contact_name}! Gostaríamos de saber como foi seu atendimento na {provedor_name}. Sua opinião faz toda a diferença para melhorarmos nossos serviços!

😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente"""
        
        # Enviar mensagem baseado no canal
        success = False
        if csat_request.channel_type == 'whatsapp':
            success = _send_whatsapp_csat(csat_request, csat_message)
        elif csat_request.channel_type == 'telegram':
            success = _send_telegram_csat(csat_request, csat_message)
        
        if success:
            # Marcar como enviado
            csat_request.status = 'sent'
            csat_request.sent_at = timezone.now()
            csat_request.save()
            logger.info(f"✅ CSAT {csat_request_id} enviado com sucesso")
        else:
            logger.error(f"❌ Falha ao enviar CSAT {csat_request_id}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao enviar CSAT {csat_request_id}: {e}")


def _send_whatsapp_csat(csat_request: CSATRequest, message: str) -> bool:
    """
    Enviar mensagem CSAT via WhatsApp
    """
    try:
        from integrations.models import WhatsAppIntegration
        
        # Buscar integração WhatsApp do provedor
        whatsapp_integration = WhatsAppIntegration.objects.filter(
            provedor=csat_request.provedor
        ).first()
        
        if not whatsapp_integration:
            logger.error(f"No WhatsApp integration found for provider {csat_request.provedor.id}")
            return False
        
        # Obter dados de contato
        contact = csat_request.contact
        phone_number = contact.additional_attributes.get('sender_lid') or contact.phone
        
        if not phone_number:
            logger.error(f"No phone number found for contact {contact.id}")
            return False
        
        # Enviar via Uazapi
        client = UazapiClient(
            base_url=whatsapp_integration.settings.get('whatsapp_url') or 'https://niochat.uazapi.com',
            token=whatsapp_integration.access_token
        )
        
        result = client.enviar_mensagem(
            numero=phone_number,
            texto=message,
            instance_id=whatsapp_integration.instance_name
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp CSAT: {str(e)}")
        return False


def _send_telegram_csat(csat_request: CSATRequest, message: str) -> bool:
    """
    Enviar mensagem CSAT via Telegram
    """
    try:
        # Implementar envio via Telegram se necessário
        logger.info(f"Telegram CSAT not implemented yet for request {csat_request.id}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending Telegram CSAT: {str(e)}")
        return False