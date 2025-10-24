"""
Serviço para gerenciar CSAT (Customer Satisfaction Score)
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings


from core.models import Provedor
from .models import Conversation, Contact, CSATFeedback, CSATRequest

logger = logging.getLogger(__name__)

class CSATService:
    """
    Serviço para gerenciar coleta de feedback CSAT
    """
    
    CSAT_EMOJIS = ['😡', '😕', '😐', '🙂', '🤩']
    EMOJI_RATINGS = {
        '😡': 1,
        '😕': 2,
        '😐': 3,
        '🙂': 4,
        '🤩': 5,
    }
    DELAY_MINUTES = 2  # Tempo de espera após encerramento da conversa
    
    @classmethod
    def schedule_csat_request(cls, conversation_id: int, ended_by_user_id: int = None):
        """
        Agendar solicitação de CSAT 2 minutos após encerramento da conversa
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
            
            # Obter o timezone de Belém
            import pytz
            belem_tz = pytz.timezone('America/Belem')
            
            # Calcular horário de envio (2 minutos após encerramento)
            ended_at = timezone.now()  # UTC
            # Converter para o timezone local e adicionar o delay
            ended_at_belem = ended_at.astimezone(belem_tz)
            scheduled_send_at = ended_at_belem + timedelta(minutes=cls.DELAY_MINUTES)
            
            # Determinar canal
            channel_type = 'whatsapp'  # Default
            if conversation.inbox and hasattr(conversation.inbox, 'channel_type'):
                channel_type = conversation.inbox.channel_type
            
            # Criar solicitação de CSAT
            csat_request = CSATRequest.objects.create(
                conversation=conversation,
                contact=conversation.contact,
                provedor=conversation.inbox.provedor,
                conversation_ended_at=ended_at,  # UTC
                scheduled_send_at=scheduled_send_at,  # Horário localizado
                channel_type=channel_type,
                status='pending'
            )
            
            # Converter o horário agendado para UTC para o agendamento
            if scheduled_send_at.tzinfo is not None:
                # Se o horário já tem timezone, converter para UTC
                eta_utc = scheduled_send_at.astimezone(pytz.UTC)
            else:
                # Se não tem timezone, assumir que é local e converter para UTC
                scheduled_time_aware = belem_tz.localize(scheduled_send_at)
                eta_utc = scheduled_time_aware.astimezone(pytz.UTC)
            
            # Importar e agendar tarefa do Dramatiq
            from .tasks import send_csat_message
            
            # Agendar a tarefa usando Dramatiq com delay
            delay_seconds = int((eta_utc - datetime.now(pytz.UTC)).total_seconds())
            
            if delay_seconds > 0:
                # Usar delay do Dramatiq para agendar a tarefa
                send_csat_message.send_with_options(
                    args=[csat_request.id],
                    delay=delay_seconds * 1000  # Dramatiq usa milissegundos
                )
                logger.info(f"CSAT request scheduled for conversation {conversation_id} at {scheduled_send_at} (delay: {delay_seconds}s)")
            else:
                # Se o horário já passou, executar imediatamente
                send_csat_message.send(csat_request.id)
                logger.info(f"CSAT request sent immediately for conversation {conversation_id}")
            
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
            
            # Converter emoji para valor numérico
            rating_value = cls.EMOJI_RATINGS.get(detected_emoji)
            
            # Criar feedback CSAT
            with transaction.atomic():
                csat_feedback = CSATFeedback.objects.create(
                    conversation=conversation,
                    contact=contact,
                    provedor=conversation.inbox.provedor,
                    emoji_rating=detected_emoji,
                    rating_value=rating_value or 0,
                    channel_type=csat_request.channel_type,
                    conversation_ended_at=csat_request.conversation_ended_at,
                    response_time_minutes=int(response_time),
                    original_message=message_content,
                    feedback_sent_at=timezone.now()
                )
                
                # Atualizar status da solicitação
                csat_request.status = 'responded'
                csat_request.responded_at = timezone.now()
                csat_request.csat_feedback = csat_feedback
                csat_request.save()
                
                # Encerrar automaticamente a conversa após feedback
                try:
                    if getattr(conversation, 'status', None) != 'closed':
                        conversation.status = 'closed'
                        if hasattr(conversation, 'ended_at'):
                            conversation.ended_at = timezone.now()
                        conversation.save(update_fields=['status'] + (['ended_at'] if hasattr(conversation, 'ended_at') else []))
                except Exception:
                    # Não bloquear fluxo de CSAT se não conseguir encerrar
                    pass
            
            logger.info(f"CSAT feedback processed: {detected_emoji} from contact {contact.id}")
            return csat_feedback
            
        except Exception as e:
            logger.error(f"Error processing CSAT response: {str(e)}")
            return None
    
    @classmethod
    def get_csat_stats(cls, provedor, days: int = 30):
        """
        Obter estatísticas CSAT para o dashboard
        """
        try:
            from django.db.models import Count, Avg
            from django.utils import timezone
            
            # Se provedor é um ID, buscar o objeto
            if isinstance(provedor, int):
                provedor = Provedor.objects.get(id=provedor)
            
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
            
            # Últimos feedbacks - usar serializer para obter dados completos incluindo foto
            recent_feedbacks_queryset = feedbacks.select_related(
                'contact', 'conversation', 'provedor'
            ).order_by('-feedback_sent_at')[:10]
            
            # Usar o serializer para obter dados completos incluindo foto da Uazapi
            from .serializers import CSATFeedbackSerializer
            serializer = CSATFeedbackSerializer(recent_feedbacks_queryset, many=True)
            recent_feedbacks = serializer.data
            
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



