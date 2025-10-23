import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
import pytz
from .models import Conversation, CSATRequest, CSATFeedback
from integrations.telegram_service import TelegramService
from integrations.email_service import EmailService

logger = logging.getLogger(__name__)

class CSATAutomationService:
    """
    Serviço para automação de coleta de CSAT
    """
    
    THANK_YOU_MESSAGE = "Obrigado pelo seu feedback! Sua opinião é muito importante para nós. 😊"
    
    @classmethod
    def generate_dynamic_csat_message(cls, provedor, contact, conversation):
        """
        Gera mensagem CSAT dinâmica usando IA com contexto do cliente e provedor
        """
        cliente_nome = contact.name
        
        try:
            from core.openai_service import OpenAIService
            from core.redis_memory_service import redis_memory_service
            
            try:
                redis_conn = redis_memory_service.get_redis_sync()
                if redis_conn:
                    key = f"conversation:{provedor.id}:{conversation.id}"
                    memory_data = redis_conn.get(key)
                    if memory_data:
                        memory = json.loads(memory_data)
                        if memory.get('nome_cliente'):
                            nome_completo = memory['nome_cliente']
                            cliente_nome = nome_completo.split()[0] if nome_completo else contact.name
                            logger.info(f"Nome do cliente encontrado na memória Redis: {cliente_nome}")
                else:
                    logger.warning("Conexão Redis não disponível")
            except Exception as e:
                logger.warning(f"Erro ao buscar nome na memória Redis: {e}")
            
            context = f"""Você é um assistente da {provedor.nome} solicitando feedback CSAT.

TAREFA: Criar uma mensagem personalizada para {cliente_nome} pedindo avaliação do atendimento.

FORMATO OBRIGATÓRIO:
1. Cumprimente de forma amigável: "Olá {cliente_nome}!"
2. Mencione a empresa: "{provedor.nome}"
3. Peça feedback de forma natural e cordial
4. SEMPRE termine com esta linha EXATA (copie exatamente):
😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente

EXEMPLO:
Olá {cliente_nome}! Como foi sua experiência com nosso atendimento da {provedor.nome}? Sua opinião é muito importante para nós!

😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente

IMPORTANTE:
- Use no máximo 3 linhas
- Seja cordial e natural
- Não use emojis extras além dos obrigatórios
- Mantenha o tom da {provedor.nome}"""

            openai_service = OpenAIService()
            response = openai_service.generate_response_sync(
                mensagem=context,
                provedor=provedor,
                contexto={'contact': contact, 'conversation': conversation}
            )

            ai_message = response.get('resposta', '') if isinstance(response, dict) else str(response)
            required_emojis = ['😡', '😕', '😐', '🙂', '🤩']
            missing_emojis = [emoji for emoji in required_emojis if emoji not in ai_message]

            if missing_emojis:
                logger.warning(f"IA não incluiu emojis CSAT: {missing_emojis}.")
                return cls._get_fallback_message(provedor, contact, cliente_nome)
            
            return ai_message.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar mensagem CSAT dinâmica: {e}")
            return cls._get_fallback_message(provedor, contact, cliente_nome)
    
    @classmethod
    def _analyze_feedback_with_ai(cls, feedback_text, provedor):
        """
        Usa IA para analisar sentimento do feedback e determinar rating CSAT
        """
        try:
            from core.openai_service import OpenAIService
            import re

            context = f"""Você é um analisador de sentimento especializado em CSAT (Customer Satisfaction).

TAREFA: Analisar o feedback do cliente e determinar o rating CSAT de 1 a 5.

FEEDBACK DO CLIENTE: "{feedback_text}"

ESCALA CSAT:
1 = 😡 Muito insatisfeito
2 = 😕 Insatisfeito
3 = 😐 Neutro
4 = 🙂 Satisfeito
5 = 🤩 Muito satisfeito

Responda APENAS com um número de 1 a 5:"""

            openai_service = OpenAIService()
            response = openai_service.generate_response_sync(
                mensagem=context,
                provedor=provedor,
                contexto={'feedback_analysis': True}
            )
            
            ai_response = response.get('resposta', '') if isinstance(response, dict) else str(response)
            rating_match = re.search(r'[1-5]', ai_response)

            if rating_match:
                rating_value = int(rating_match.group())
                emoji_map = {1: '😡', 2: '😕', 3: '😐', 4: '🙂', 5: '🤩'}
                return {'rating': rating_value, 'emoji': emoji_map[rating_value], 'ai_response': ai_response.strip()}
            return None
                
        except Exception as e:
            logger.error(f"Erro na análise de sentimento por IA: {e}")
            return None
    
    @classmethod
    def _get_fallback_message(cls, provedor, contact, cliente_nome=None):
        nome_usar = cliente_nome or contact.name
        return f"""Olá {nome_usar}! Como foi sua experiência com o atendimento da {provedor.nome}?

Pode deixar sua opinião em uma única mensagem:
😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente"""
    
    EMOJI_RATINGS = {'😡': 1, '😕': 2, '😐': 3, '🙂': 4, '🤩': 5}
    
    @classmethod
    def create_csat_request(cls, conversation):
        """
        Cria uma solicitação de CSAT para conversa encerrada
        """
        try:
            existing_request = CSATRequest.objects.filter(conversation=conversation).first()
            if existing_request:
                return existing_request
            
            twelve_hours_ago = timezone.now() - timedelta(hours=12)
            recent_csat = CSATRequest.objects.filter(
                contact=conversation.contact,
                created_at__gte=twelve_hours_ago
            ).exists()
            
            if recent_csat:
                return None
            
            # Obter o timezone de São Paulo
            sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
            
            # Obter horário atual em UTC e converter para São Paulo
            current_time_utc = timezone.now()
            current_time_sp = current_time_utc.astimezone(sao_paulo_tz)
            
            # Agendar para 90 segundos a partir de agora (no timezone local)
            scheduled_time = current_time_sp + timedelta(seconds=90)
            
            csat_request = CSATRequest.objects.create(
                conversation=conversation,
                contact=conversation.contact,
                provedor=conversation.inbox.provedor,
                channel_type=conversation.inbox.channel_type,
                status='pending',
                conversation_ended_at=current_time_utc,  # Manter o horário de término em UTC
                scheduled_send_at=scheduled_time  # Horário agendado em timezone local
            )
            
            # Executar task imediatamente com delay interno
            from .tasks import send_csat_message
            send_csat_message.apply_async(args=[csat_request.id], countdown=90)
            return csat_request
            
        except Exception as e:
            logger.error(f"Erro ao criar CSAT request: {e}")
            return None
    
    @classmethod
    def send_csat_message(cls, csat_request_id):
        """
        Envia mensagem de solicitação de CSAT
        """
        try:
            csat_request = CSATRequest.objects.get(id=csat_request_id)
            conversation = csat_request.conversation
            contact = csat_request.contact
            provedor = csat_request.provedor
            
            if conversation.status != 'closed':
                csat_request.status = 'cancelled'
                csat_request.save()
                return False
            
            dynamic_message = cls.generate_dynamic_csat_message(provedor, contact, conversation)
            success = False
            
            if csat_request.channel_type == 'whatsapp':
                success = cls._send_whatsapp_message(provedor, contact, dynamic_message)
            elif csat_request.channel_type == 'telegram':
                success = cls._send_telegram_message(provedor, contact, dynamic_message)
            elif csat_request.channel_type == 'email':
                success = cls._send_email_message(provedor, contact, dynamic_message)
            
            csat_request.status = 'sent' if success else 'failed'
            csat_request.sent_at = timezone.now() if success else None
            csat_request.save()
            return success
                
        except Exception as e:
            logger.error(f"Erro ao enviar CSAT message: {e}")
            return False

    @classmethod
    def process_csat_response(cls, message_text, conversation, contact):
        """
        Processa resposta de CSAT do cliente
        """
        try:
            csat_request = CSATRequest.objects.filter(conversation=conversation, status='sent').first()
            if not csat_request:
                return None
            
            existing_feedback = CSATFeedback.objects.filter(conversation=conversation).first()
            if existing_feedback:
                return existing_feedback
            
            emoji_rating, rating_value = None, None
            for emoji, value in cls.EMOJI_RATINGS.items():
                if emoji in message_text:
                    emoji_rating, rating_value = emoji, value
                    break
            
            if not emoji_rating:
                ai_analysis = cls._analyze_feedback_with_ai(message_text, csat_request.provedor)
                if ai_analysis:
                    emoji_rating, rating_value = ai_analysis['emoji'], ai_analysis['rating']
            
            if not emoji_rating:
                emoji_rating, rating_value = '😐', 3
            
            response_time = timezone.now() - csat_request.conversation_ended_at
            response_time_minutes = int(response_time.total_seconds() / 60)
            
            feedback = CSATFeedback.objects.create(
                conversation=conversation,
                contact=contact,
                provedor=csat_request.provedor,
                emoji_rating=emoji_rating,
                rating_value=rating_value,
                original_message=message_text,
                channel_type=csat_request.channel_type,
                conversation_ended_at=csat_request.conversation_ended_at,
                response_time_minutes=response_time_minutes
            )
            
            csat_request.status = 'completed'
            csat_request.completed_at = timezone.now()
            csat_request.save()

            from core.models import AuditLog
            audit_log = AuditLog.objects.filter(
                conversation_id=conversation.id,
                action__in=['conversation_closed_agent', 'conversation_closed_ai']
            ).first()
            if audit_log:
                audit_log.csat_rating = rating_value
                audit_log.save()
            
            # Salvar no Supabase
            try:
                from core.supabase_service import SupabaseService
                supabase_service = SupabaseService()
                supabase_service.save_csat(
                    provedor_id=csat_request.provedor.id,
                    conversation_id=conversation.id,
                    contact_id=contact.id,
                    emoji_rating=emoji_rating,
                    rating_value=rating_value,
                    feedback_sent_at_iso=timezone.now().isoformat()
                )
                logger.info(f"✅ CSAT enviado para Supabase: conversa {conversation.id} - Rating: {rating_value}")
            except Exception as e:
                logger.error(f"Falha ao enviar CSAT para Supabase: {e}")
            
            cls._send_thank_you_message(csat_request, contact)
            return feedback
            
        except Exception as e:
            logger.error(f"Erro ao processar CSAT response: {e}")
            return None

    @classmethod
    def _send_thank_you_message(cls, csat_request, contact):
        try:
            provedor = csat_request.provedor
            if csat_request.channel_type == 'whatsapp':
                cls._send_whatsapp_message(provedor, contact, cls.THANK_YOU_MESSAGE)
            elif csat_request.channel_type == 'telegram':
                cls._send_telegram_message(provedor, contact, cls.THANK_YOU_MESSAGE)
            elif csat_request.channel_type == 'email':
                cls._send_email_message(provedor, contact, cls.THANK_YOU_MESSAGE)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de agradecimento: {e}")

    @classmethod
    def _send_whatsapp_message(cls, provedor, contact, message):
        try:
            from core.uazapi_client import UazapiClient
            config = provedor.integracoes_externas
            client = UazapiClient(config.get('whatsapp_url'), config.get('whatsapp_token'))
            return client.enviar_mensagem(
                numero=contact.phone,
                texto=message,
                instance_id=config.get('whatsapp_instance')
            )
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp message: {e}")
            return False
