import logging
import json
from datetime import datetime, timedelta
from django.utils import timezone
from celery import shared_task
from .models import Conversation, CSATRequest, CSATFeedback
# WhatsAppService removido - usando UazapiClient
from integrations.telegram_service import TelegramService
from integrations.email_service import EmailService

logger = logging.getLogger(__name__)

class CSATAutomationService:
    """
    Serviço para automação de coleta de CSAT
    """
    
    # Mensagem de agradecimento ainda pode ser fixa ou também pode ser dinâmica
    THANK_YOU_MESSAGE = "Obrigado pelo seu feedback! Sua opinião é muito importante para nós. 😊"
    
    @classmethod
    def generate_dynamic_csat_message(cls, provedor, contact, conversation):
        """
        Gera mensagem CSAT dinâmica usando IA com contexto do cliente e provedor
        Usa o primeiro nome do cliente da memória Redis (SGP) quando disponível
        """
        # Buscar nome do cliente na memória Redis
        cliente_nome = contact.name  # Fallback para nome do contato
        
        try:
            from core.openai_service import OpenAIService
            from core.redis_memory_service import redis_memory_service
            import asyncio
            
            try:
                # Buscar memória usando conexão síncrona
                redis_conn = redis_memory_service.get_redis_sync()
                if redis_conn:
                    key = f"conversation:{provedor.id}:{conversation.id}"
                    memory_data = redis_conn.get(key)
                    
                    if memory_data:
                        import json
                        memory = json.loads(memory_data)
                        
                        if memory.get('nome_cliente'):
                            nome_completo = memory['nome_cliente']
                            # Extrair apenas o primeiro nome
                            primeiro_nome = nome_completo.split()[0] if nome_completo else contact.name
                            cliente_nome = primeiro_nome
                            logger.info(f"Nome do cliente encontrado na memória Redis: {nome_completo} -> {primeiro_nome}")
                        else:
                            logger.info("Campo 'nome_cliente' não encontrado na memória Redis")
                    else:
                        logger.info(f"Nenhuma memória encontrada para conversa {conversation.id}")
                else:
                    logger.warning("Conexão Redis não disponível")
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar nome na memória Redis: {e}. Usando nome do contato.")
                cliente_nome = contact.name
            
            # Contexto para a IA
            context = f"""Você é um assistente da {provedor.nome} solicitando feedback CSAT.

TAREFA: Criar uma mensagem personalizada para {cliente_nome} pedindo avaliação do atendimento.

FORMATO OBRIGATÓRIO:
1. Cumprimente: "Olá {cliente_nome}!"
2. Mencione a empresa: "{provedor.nome}"
3. Peça feedback de forma amigável
4. SEMPRE termine com esta linha EXATA (copie exatamente):
😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente

EXEMPLO:
Olá {cliente_nome}! Como foi sua experiência com nosso atendimento da {provedor.nome}? Sua opinião é muito importante para nós!

😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente

IMPORTANTE: Use no máximo 3 linhas e seja cordial."""

            # Gerar mensagem usando IA
            openai_service = OpenAIService()
            response = openai_service.generate_response_sync(
                mensagem=context,
                provedor=provedor,
                contexto={'contact': contact, 'conversation': conversation}
            )
            
            # Extrair mensagem da resposta
            ai_message = response.get('resposta', '') if isinstance(response, dict) else str(response)
            
            # Verificar se a mensagem contém os emojis obrigatórios
            required_emojis = ['😡', '😕', '😐', '🙂', '🤩']
            missing_emojis = [emoji for emoji in required_emojis if emoji not in ai_message]
            
            if missing_emojis:
                logger.warning(f"IA não incluiu emojis CSAT: {missing_emojis}. Mensagem IA: {ai_message[:200]}...")
                return cls._get_fallback_message(provedor, contact, cliente_nome)
            
            logger.info(f"Mensagem CSAT gerada pela IA: {ai_message[:100]}...")
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
            
            # Prompt específico para análise de sentimento CSAT
            context = f"""Você é um analisador de sentimento especializado em CSAT (Customer Satisfaction).

TAREFA: Analisar o feedback do cliente e determinar o rating CSAT de 1 a 5.

FEEDBACK DO CLIENTE: "{feedback_text}"

ESCALA CSAT:
1 = 😡 Muito insatisfeito (péssimo, horrível, terrível)
2 = 😕 Insatisfeito (ruim, não gostei, problemas)
3 = 😐 Neutro (regular, ok, normal, mais ou menos)
4 = 🙂 Satisfeito (bom, gostei, legal, positivo)
5 = 🤩 Muito satisfeito (excelente, ótimo, perfeito, amei)

INSTRUÇÕES:
1. Analise o sentimento geral da mensagem
2. Considere contexto de atendimento ao cliente
3. Se mencionar problemas específicos (IA rápida demais, termos técnicos), considere como feedback construtivo
4. Responda APENAS com um número de 1 a 5
5. Se não conseguir determinar, use 3 (neutro)

RESPOSTA (apenas o número):"""

            # Gerar análise usando IA
            openai_service = OpenAIService()
            response = openai_service.generate_response_sync(
                mensagem=context,
                provedor=provedor,
                contexto={'feedback_analysis': True}
            )
            
            # Extrair rating da resposta
            ai_response = response.get('resposta', '') if isinstance(response, dict) else str(response)
            
            # Tentar extrair número da resposta
            import re
            rating_match = re.search(r'[1-5]', ai_response)
            
            if rating_match:
                rating_value = int(rating_match.group())
                
                # Mapear rating para emoji
                emoji_map = {
                    1: '😡',
                    2: '😕', 
                    3: '😐',
                    4: '🙂',
                    5: '🤩'
                }
                
                return {
                    'rating': rating_value,
                    'emoji': emoji_map[rating_value],
                    'ai_response': ai_response.strip()
                }
            else:
                logger.warning(f"IA não retornou rating válido: {ai_response}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na análise de sentimento por IA: {e}")
            return None
    
    @classmethod
    def _get_fallback_message(cls, provedor, contact, cliente_nome=None):
        """
        Mensagem de fallback personalizada caso a IA falhe
        """
        nome_usar = cliente_nome or contact.name
        return f"""Olá {nome_usar}! Como foi sua experiência com o atendimento da {provedor.nome}?

Pode deixar sua opinião em uma única mensagem:
😡 Péssimo | 😕 Ruim | 😐 Regular | 🙂 Bom | 🤩 Excelente"""
    
    EMOJI_RATINGS = {
        '😡': 1,
        '😕': 2, 
        '😐': 3,
        '🙂': 4,
        '🤩': 5
    }
    
    @classmethod
    def create_csat_request(cls, conversation):
        """
        Cria uma solicitação de CSAT para uma conversa encerrada
        A mensagem será enviada 2 minutos após o encerramento
        """
        try:
            # Verificar se já existe uma solicitação para esta conversa
            existing_request = CSATRequest.objects.filter(conversation=conversation).first()
            if existing_request:
                logger.info(f"CSAT request já existe para conversa {conversation.id}")
                return existing_request
            
            # Criar nova solicitação
            csat_request = CSATRequest.objects.create(
                conversation=conversation,
                contact=conversation.contact,
                provedor=conversation.inbox.provedor,
                channel_type=conversation.inbox.channel_type,
                status='pending',
                conversation_ended_at=timezone.now(),
                scheduled_send_at=timezone.now() + timedelta(minutes=2)  # 2 minutos após encerramento
            )
            
            logger.info(f"CSAT request criada: {csat_request.id} para conversa {conversation.id}")
            
            # Agendar envio da mensagem
            from .tasks import send_csat_message
            send_csat_message.apply_async(
                args=[csat_request.id],
                eta=csat_request.scheduled_send_at
            )
            
            return csat_request
            
        except Exception as e:
            logger.error(f"Erro ao criar CSAT request: {e}")
            return None
    
    @classmethod
    def send_csat_message(cls, csat_request):
        """
        Envia mensagem de solicitação de CSAT
        """
        try:
            conversation = csat_request.conversation
            contact = csat_request.contact
            provedor = csat_request.provedor
            
            # Verificar se a conversa ainda está fechada (não foi reaberta)
            if conversation.status != 'closed':
                logger.info(f"Conversa {conversation.id} foi reaberta, cancelando CSAT")
                csat_request.status = 'cancelled'
                csat_request.save()
                return False
            
            # Gerar mensagem CSAT dinâmica usando IA
            dynamic_message = cls.generate_dynamic_csat_message(provedor, contact, conversation)
            
            # Enviar mensagem baseado no canal
            success = False
            
            if csat_request.channel_type == 'whatsapp':
                success = cls._send_whatsapp_message(provedor, contact, dynamic_message)
            elif csat_request.channel_type == 'telegram':
                success = cls._send_telegram_message(provedor, contact, dynamic_message)
            elif csat_request.channel_type == 'email':
                success = cls._send_email_message(provedor, contact, dynamic_message)
            
            if success:
                csat_request.status = 'sent'
                csat_request.sent_at = timezone.now()
                csat_request.save()
                logger.info(f"CSAT message enviada para conversa {conversation.id}")
                return True
            else:
                csat_request.status = 'failed'
                csat_request.save()
                logger.error(f"Falha ao enviar CSAT message para conversa {conversation.id}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar CSAT message: {e}")
            csat_request.status = 'failed'
            csat_request.save()
            return False
    
    @classmethod
    def process_csat_response(cls, message_text, conversation, contact):
        """
        Processa resposta de CSAT do cliente
        """
        try:
            # Buscar solicitação CSAT pendente
            csat_request = CSATRequest.objects.filter(
                conversation=conversation,
                status='sent'
            ).first()
            
            if not csat_request:
                logger.info(f"Nenhuma solicitação CSAT pendente para conversa {conversation.id}")
                return None
            
            # Verificar se já existe feedback
            existing_feedback = CSATFeedback.objects.filter(conversation=conversation).first()
            if existing_feedback:
                logger.info(f"Feedback já existe para conversa {conversation.id}")
                return existing_feedback
            
            # Extrair emoji da mensagem
            emoji_rating = None
            rating_value = None
            
            for emoji, value in cls.EMOJI_RATINGS.items():
                if emoji in message_text:
                    emoji_rating = emoji
                    rating_value = value
                    break
            
            # Se não encontrou emoji, usar IA para analisar sentimento
            if not emoji_rating:
                ai_analysis = cls._analyze_feedback_with_ai(message_text, csat_request.provedor)
                if ai_analysis:
                    emoji_rating = ai_analysis['emoji']
                    rating_value = ai_analysis['rating']
                    logger.info(f"IA analisou feedback: '{message_text}' -> {emoji_rating} (rating {rating_value})")
                else:
                    # Fallback para palavras-chave básicas
                    message_lower = message_text.lower()
                    if any(word in message_lower for word in ['péssimo', 'horrível', 'terrível', 'ruim', 'não gostei']):
                        emoji_rating = '😕'
                        rating_value = 2
                    elif any(word in message_lower for word in ['regular', 'ok', 'normal', 'mais ou menos']):
                        emoji_rating = '😐'
                        rating_value = 3
                    elif any(word in message_lower for word in ['bom', 'boa', 'gostei', 'legal']):
                        emoji_rating = '🙂'
                        rating_value = 4
                    elif any(word in message_lower for word in ['excelente', 'ótimo', 'perfeito', 'maravilhoso', 'amei']):
                        emoji_rating = '🤩'
                        rating_value = 5
            
            # Se ainda não conseguiu identificar, assumir rating neutro
            if not emoji_rating:
                emoji_rating = '😐'
                rating_value = 3
            
            # Calcular tempo de resposta
            response_time = timezone.now() - csat_request.conversation_ended_at
            response_time_minutes = int(response_time.total_seconds() / 60)
            
            # Criar feedback
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
            
            # Atualizar status da solicitação
            csat_request.status = 'completed'
            csat_request.completed_at = timezone.now()
            csat_request.save()
            
            # Atualizar AuditLog com o rating CSAT
            from core.models import AuditLog
            try:
                audit_log = AuditLog.objects.filter(
                    conversation_id=conversation.id,
                    action__in=['conversation_closed_agent', 'conversation_closed_ai']
                ).first()
                
                if audit_log:
                    audit_log.csat_rating = rating_value
                    audit_log.save()
                    logger.info(f"AuditLog {audit_log.id} atualizado com CSAT rating {rating_value}")
                else:
                    logger.warning(f"AuditLog não encontrado para conversa {conversation.id}")
            except Exception as e:
                logger.error(f"Erro ao atualizar AuditLog com CSAT: {e}")
            
            logger.info(f"CSAT feedback criado: {feedback.id} com rating {rating_value}")
            
            # Enviar mensagem de agradecimento
            cls._send_thank_you_message(csat_request, contact)
            
            return feedback
            
        except Exception as e:
            logger.error(f"Erro ao processar CSAT response: {e}")
            return None
    
    @classmethod
    def send_thank_you_message(cls, provedor, contact):
        """
        Método público para enviar mensagem de agradecimento
        """
        try:
            # Determinar canal (assumir WhatsApp por padrão)
            channel_type = 'whatsapp'
            
            if channel_type == 'whatsapp':
                return cls._send_whatsapp_message(provedor, contact, cls.THANK_YOU_MESSAGE)
            elif channel_type == 'telegram':
                return cls._send_telegram_message(provedor, contact, cls.THANK_YOU_MESSAGE)
            elif channel_type == 'email':
                return cls._send_email_message(provedor, contact, cls.THANK_YOU_MESSAGE)
            
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar agradecimento: {e}")
            return False
    
    @classmethod
    def _send_thank_you_message(cls, csat_request, contact):
        """
        Envia mensagem de agradecimento (apenas uma vez)
        """
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
        """
        Envia mensagem via WhatsApp usando UazapiClient
        """
        try:
            from core.uazapi_client import UazapiClient
            
            # Obter configurações do provedor
            config = provedor.integracoes_externas
            whatsapp_url = config.get('whatsapp_url')
            whatsapp_token = config.get('whatsapp_token')
            whatsapp_instance = config.get('whatsapp_instance')
            
            if not whatsapp_url or not whatsapp_token:
                logger.error(f"Configurações WhatsApp não encontradas para provedor {provedor.id}")
                return False
            
            # Criar cliente Uazapi
            client = UazapiClient(whatsapp_url, whatsapp_token)
            
            # Enviar mensagem
            result = client.enviar_mensagem(
                numero=contact.phone,
                texto=message,
                instance_id=whatsapp_instance
            )
            
            logger.info(f"Mensagem CSAT enviada via UazapiClient: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp message via UazapiClient: {e}")
            return False
    
    @classmethod
    def _send_telegram_message(cls, provedor, contact, message):
        """
        Envia mensagem via Telegram
        """
        try:
            from integrations.telegram_service import TelegramService
            from integrations.models import TelegramIntegration
            
            # Buscar integração Telegram do provedor
            telegram_integration = TelegramIntegration.objects.filter(company=provedor).first()
            if not telegram_integration:
                logger.error("Integração Telegram não encontrada")
                return False
            
            telegram_service = TelegramService(telegram_integration)
            
            # Buscar telegram_id do contato
            telegram_id = contact.additional_attributes.get('telegram_id')
            if not telegram_id:
                logger.error("Telegram ID não encontrado no contato")
                return False
            
            import asyncio
            return asyncio.run(telegram_service.send_message(telegram_id, message))
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram message: {e}")
            return False
    
    @classmethod
    def _send_email_message(cls, provedor, contact, message):
        """
        Envia mensagem via Email
        """
        try:
            from integrations.email_service import EmailService
            from integrations.models import EmailIntegration
            
            # Buscar integração Email do provedor
            email_integration = EmailIntegration.objects.filter(company=provedor).first()
            if not email_integration:
                logger.error("Integração Email não encontrada")
                return False
            
            email_service = EmailService(email_integration)
            return email_service.send_email(contact.email, "Avaliação do Atendimento", message)
        except Exception as e:
            logger.error(f"Erro ao enviar Email message: {e}")
            return False


# Task movida para conversations/tasks.py
