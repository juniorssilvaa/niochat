"""
Serviço para gerenciar CSAT (Customer Satisfaction Score)
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from celery import shared_task

from core.models import Provedor
from .models import Conversation, Contact, CSATFeedback, CSATRequest

logger = logging.getLogger(__name__)

class CSATService:
    """
    Serviço para gerenciar coleta de feedback CSAT
    """
    
    CSAT_EMOJIS = ['😡', '😕', '😐', '🙂', '🤩']
    DELAY_MINUTES = 3  # Tempo de espera após encerramento da conversa
    
    @classmethod
    def schedule_csat_request(cls, conversation_id: int, ended_by_user_id: int = None):
        """
        Agendar solicitação de CSAT 3 minutos após encerramento da conversa
        """
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Verificar se já existe uma solicitação para esta conversa
            existing_request = CSATRequest.objects.filter(
                conversation=conversation
            ).first()
            
            if existing_request:
                logger.info(f"CSAT request already exists for conversation {conversation_id}")
                return existing_request
            
            # Calcular horário de envio (3 minutos após encerramento)
            ended_at = timezone.now()
            scheduled_send_at = ended_at + timedelta(minutes=cls.DELAY_MINUTES)
            
            # Determinar canal
            channel_type = 'whatsapp'  # Default
            if conversation.inbox and hasattr(conversation.inbox, 'channel_type'):
                channel_type = conversation.inbox.channel_type
            
            # Criar solicitação de CSAT
            csat_request = CSATRequest.objects.create(
                conversation=conversation,
                contact=conversation.contact,
                provedor=conversation.inbox.provedor,
                conversation_ended_at=ended_at,
                scheduled_send_at=scheduled_send_at,
                channel_type=channel_type,
                status='pending'
            )
            
            # Agendar tarefa Celery para envio
            send_csat_message.apply_async(
                args=[csat_request.id],
                eta=scheduled_send_at
            )
            
            logger.info(f"CSAT request scheduled for conversation {conversation_id} at {scheduled_send_at}")
            return csat_request
            
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conversation_id} not found for CSAT scheduling")
            return None
        except Exception as e:
            logger.error(f"Error scheduling CSAT request: {str(e)}")
            return None
    
    @classmethod
    def process_csat_response(cls, message_content: str, contact: Contact, conversation: Conversation):
        """
        Processar resposta de CSAT baseada em emoji
        """
        try:
            # Buscar emoji na mensagem
            detected_emoji = None
            for emoji in cls.CSAT_EMOJIS:
                if emoji in message_content:
                    detected_emoji = emoji
                    break
            
            if not detected_emoji:
                logger.info(f"No CSAT emoji detected in message: {message_content}")
                return None
            
            # Buscar solicitação de CSAT pendente
            csat_request = CSATRequest.objects.filter(
                contact=contact,
                status__in=['pending', 'sent'],
                conversation=conversation
            ).first()
            
            if not csat_request:
                logger.info(f"No pending CSAT request found for contact {contact.id}")
                return None
            
            # Calcular tempo de resposta
            response_time = (timezone.now() - csat_request.sent_at).total_seconds() / 60 if csat_request.sent_at else 0
            
            # Criar feedback CSAT
            with transaction.atomic():
                csat_feedback = CSATFeedback.objects.create(
                    conversation=conversation,
                    contact=contact,
                    provedor=conversation.inbox.provedor,
                    emoji_rating=detected_emoji,
                    channel_type=csat_request.channel_type,
                    conversation_ended_at=csat_request.conversation_ended_at,
                    response_time_minutes=int(response_time),
                    original_message=message_content
                )
                
                # Atualizar status da solicitação
                csat_request.status = 'responded'
                csat_request.responded_at = timezone.now()
                csat_request.csat_feedback = csat_feedback
                csat_request.save()
            
            logger.info(f"CSAT feedback processed: {detected_emoji} from contact {contact.id}")
            return csat_feedback
            
        except Exception as e:
            logger.error(f"Error processing CSAT response: {str(e)}")
            return None
    
    @classmethod
    def get_csat_stats(cls, provedor: Provedor, days: int = 30):
        """
        Obter estatísticas CSAT para o dashboard
        """
        try:
            from django.db.models import Count, Avg
            from django.utils import timezone
            
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Feedbacks no período
            feedbacks = CSATFeedback.objects.filter(
                provedor=provedor,
                feedback_sent_at__gte=start_date,
                feedback_sent_at__lte=end_date
            )
            
            # Estatísticas básicas
            total_feedbacks = feedbacks.count()
            average_rating = feedbacks.aggregate(avg=Avg('rating_value'))['avg'] or 0
            
            # Distribuição por rating
            rating_distribution = feedbacks.values('emoji_rating', 'rating_value').annotate(
                count=Count('id')
            ).order_by('rating_value')
            
            # Distribuição por canal
            channel_distribution = feedbacks.values('channel_type').annotate(
                count=Count('id')
            ).order_by('channel_type')
            
            # Taxa de satisfação (ratings 4 e 5)
            satisfied_count = feedbacks.filter(rating_value__gte=4).count()
            satisfaction_rate = (satisfied_count / total_feedbacks * 100) if total_feedbacks > 0 else 0
            
            # Tendência diária - evolução da satisfação média
            daily_stats = feedbacks.extra(
                select={'day': "date(feedback_sent_at)"}
            ).values('day').annotate(
                count=Count('id'),
                avg_rating=Avg('rating_value')
            ).order_by('day')
            
            # Garantir que temos dados para todos os dias no período (para gráfico contínuo)
            daily_stats_dict = {item['day']: item for item in daily_stats}
            complete_daily_stats = []
            
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.strftime('%Y-%m-%d')
                if date_str in daily_stats_dict:
                    complete_daily_stats.append(daily_stats_dict[date_str])
                else:
                    # Adicionar dia sem dados
                    complete_daily_stats.append({
                        'day': date_str,
                        'count': 0,
                        'avg_rating': 0
                    })
                current_date += timedelta(days=1)
            
            # Últimos feedbacks
            recent_feedbacks = list(feedbacks.select_related(
                'contact', 'conversation', 'provedor'
            ).order_by('-feedback_sent_at')[:10])
            
            return {
                'total_feedbacks': total_feedbacks,
                'average_rating': round(average_rating, 1),
                'satisfaction_rate': round(satisfaction_rate),
                'rating_distribution': list(rating_distribution),
                'channel_distribution': list(channel_distribution),
                'daily_stats': complete_daily_stats,
                'recent_feedbacks': recent_feedbacks
            }
            
        except Exception as e:
            logger.error(f"Error getting CSAT stats: {str(e)}")
            return {}


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
        
        csat_message = f"""Olá! Como foi seu atendimento conosco?

Por favor, responda com um emoji:
😡 - Muito insatisfeito
😕 - Insatisfeito  
😐 - Neutro
🙂 - Satisfeito
🤩 - Muito satisfeito

Sua opinião é muito importante para nós! 💙"""
        
        # Enviar mensagem baseado no canal
        success = False
        if csat_request.channel_type == 'whatsapp':
            success = _send_whatsapp_csat(csat_request, csat_message)
        elif csat_request.channel_type == 'telegram':
            success = _send_telegram_csat(csat_request, csat_message)
        # Adicionar outros canais conforme necessário
        
        if success:
            csat_request.status = 'sent'
            csat_request.sent_at = timezone.now()
            csat_request.save()
            logger.info(f"CSAT message sent successfully for request {csat_request_id}")
        else:
            logger.error(f"Failed to send CSAT message for request {csat_request_id}")
            
    except CSATRequest.DoesNotExist:
        logger.error(f"CSAT request {csat_request_id} not found")
    except Exception as e:
        logger.error(f"Error sending CSAT message: {str(e)}")


def _send_whatsapp_csat(csat_request: CSATRequest, message: str) -> bool:
    """
    Enviar mensagem CSAT via WhatsApp
    """
    try:
        from core.uazapi_client import UazapiClient
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
        phone_number = contact.additional_attributes.get('sender_lid') or contact.phone_number
        
        if not phone_number:
            logger.error(f"No phone number found for contact {contact.id}")
            return False
        
        # Enviar via Uazapi
        client = UazapiClient(
            base_url=whatsapp_integration.settings.get('whatsapp_url'),
            token=whatsapp_integration.access_token
        )
        
        result = client.send_text_message(
            instance=whatsapp_integration.instance_id,
            phone=phone_number,
            text=message
        )
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp CSAT: {str(e)}")
        return False


def _send_telegram_csat(csat_request: CSATRequest, message: str) -> bool:
    """
    Enviar mensagem CSAT via Telegram
    """
    try:
        # Implementar envio via Telegram
        # Similar ao WhatsApp, usando a integração Telegram
        logger.info("Telegram CSAT sending not implemented yet")
        return False
        
    except Exception as e:
        logger.error(f"Error sending Telegram CSAT: {str(e)}")
        return False
