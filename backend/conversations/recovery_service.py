"""
Serviço de Recuperação de Conversas
Analisa conversas para identificar clientes interessados em contratar planos
"""
import logging
from typing import List, Dict, Optional
from django.utils import timezone
from datetime import timedelta
from conversations.models import Conversation, Message
from core.openai_service import OpenAIService
from core.uazapi_client import UazapiClient
from .models import RecoveryAttempt, RecoverySettings

logger = logging.getLogger(__name__)

class ConversationRecoveryService:
    """Serviço para recuperação de conversas com IA"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        # UazapiClient será inicializado quando necessário
        self.uazapi_client = None
    
    def get_provider_settings(self, provider_id: int) -> RecoverySettings:
        """
        Busca as configurações de recuperação do provedor
        
        Args:
            provider_id: ID do provedor
            
        Returns:
            Objeto RecoverySettings ou configurações padrão
        """
        try:
            from core.models import Provedor
            provider = Provedor.objects.get(id=provider_id)
            settings, created = RecoverySettings.objects.get_or_create(
                provedor=provider,
                defaults={
                    'enabled': True,
                    'delay_minutes': 30,
                    'max_attempts': 3,
                    'auto_discount': False,
                    'discount_percentage': 10,
                    'keywords': ['plano', 'internet', 'velocidade', 'preço']
                }
            )
            return settings
        except Exception as e:
            logger.error(f"Erro ao buscar configurações do provedor {provider_id}: {e}")
            # Retornar configurações padrão
            return RecoverySettings(
                enabled=True,
                delay_minutes=30,
                max_attempts=3,
                auto_discount=False,
                discount_percentage=10,
                keywords=['plano', 'internet', 'velocidade', 'preço']
            )
    
    def analyze_provider_conversations(self, provider_id: int, days_back: int = 7) -> List[Dict]:
        """
        Analisa conversas do provedor para identificar clientes interessados em contratar
        
        Args:
            provider_id: ID do provedor
            days_back: Quantos dias atrás analisar
            
        Returns:
            Lista de conversas com potencial de recuperação
        """
        try:
            # Buscar configurações do provedor
            settings = self.get_provider_settings(provider_id)
            
            # Buscar conversas dos últimos dias que estão ATIVAS mas sem agente atribuído
            start_date = timezone.now() - timedelta(days=days_back)
            
            conversations = Conversation.objects.filter(
                inbox__provedor_id=provider_id,
                created_at__gte=start_date,
                status__in=['open', 'snoozed'],  # Conversas ativas ou pausadas
                assignee=None  # Sem agente atribuído (IA livre)
            ).order_by('-created_at')
            
            recovery_candidates = []
            
            for conversation in conversations:
                # Verificar se o cliente está inativo há mais tempo que o delay configurado
                last_message = conversation.messages.filter(is_from_customer=True).order_by('-created_at').first()
                if not last_message:
                    continue
                
                # Calcular tempo de inatividade
                time_since_last_message = timezone.now() - last_message.created_at
                delay_minutes = settings.delay_minutes
                
                # Só processar se o cliente está inativo há mais tempo que o delay
                if time_since_last_message.total_seconds() < (delay_minutes * 60):
                    continue
                
                # Analisar se a conversa tem potencial de recuperação (mencionou planos)
                analysis = self._analyze_conversation_for_recovery(conversation, settings)
                
                
                # A análise pode retornar uma lista ou dicionário
                if isinstance(analysis, list) and len(analysis) > 0:
                    analysis = analysis[0]  # Pegar o primeiro item da lista
                
                if isinstance(analysis, dict) and analysis.get('has_potential', False):
                    recovery_candidates.append({
                        'conversation_id': conversation.id,
                        'contact_phone': conversation.contact.phone,
                        'contact_name': conversation.contact.name,
                        'last_message_date': conversation.updated_at,
                        'analysis': analysis,
                        'recovery_reason': analysis['reason'],
                        'provider_id': provider_id,  # Garantir isolamento por provedor
                        'inactive_minutes': int(time_since_last_message.total_seconds() / 60)
                    })
            
            logger.info(f"Encontradas {len(recovery_candidates)} conversas com potencial de recuperação para provedor {provider_id}")
            return recovery_candidates
            
        except Exception as e:
            logger.error(f"Erro ao analisar conversas do provedor {provider_id}: {e}")
            return []
    
    def _analyze_conversation_for_recovery(self, conversation: Conversation, settings: RecoverySettings) -> Dict:
        """
        Analisa uma conversa específica para determinar se tem potencial de recuperação
        
        Args:
            conversation: Objeto da conversa
            settings: Configurações do provedor
            
        Returns:
            Dicionário com análise da conversa
        """
        try:
            # Buscar mensagens da conversa
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
            
            if not messages.exists():
                return {'has_potential': False, 'reason': 'Sem mensagens'}
            
            # Preparar contexto das mensagens
            conversation_text = ""
            for msg in messages:
                if msg.content:
                    sender = "Cliente" if msg.is_from_customer else "Atendente"
                    conversation_text += f"{sender}: {msg.content}\n"
            
            # Verificar se o cliente mencionou palavras-chave de interesse
            keywords = settings.keywords or ['plano', 'internet', 'velocidade', 'preço', 'contratar', 'instalar']
            mentioned_keywords = []
            for keyword in keywords:
                if keyword.lower() in conversation_text.lower():
                    mentioned_keywords.append(keyword)
            
            # Se não mencionou nenhuma palavra-chave, não tem potencial
            if not mentioned_keywords:
                return {
                    'has_potential': False, 
                    'reason': f'Cliente não mencionou palavras-chave de interesse: {keywords}',
                    'mentioned_keywords': []
                }
            
            # Prompt para análise de IA
            prompt = f"""
            Analise esta conversa entre um provedor de internet e um cliente para determinar se há potencial de recuperação de venda.
            
            CONVERSA:
            {conversation_text}
            
            PALAVRAS-CHAVE MENCIONADAS PELO CLIENTE: {mentioned_keywords}
            
            CRITÉRIOS DE ANÁLISE:
            1. O cliente demonstrou interesse em contratar um plano de internet?
            2. O cliente fez perguntas sobre preços, planos ou instalação?
            3. O cliente mencionou problemas com internet atual ou necessidade de melhor conexão?
            4. A conversa terminou sem contratação, mas com interesse do cliente?
            5. O cliente pediu para "pensar" ou "consultar" alguém?
            6. Houve alguma barreira (preço, instalação, etc.) que impediu a contratação?
            
            Responda em JSON com:
            {{
                "has_potential": true/false,
                "interest_level": "alto/medio/baixo",
                "barriers": ["preço", "instalação", "tempo", "outros"],
                "reason": "explicação do motivo",
                "suggested_approach": "como abordar o cliente"
            }}
            """
            
            # Chamar IA para análise
            ai_response = self.openai_service.generate_response_sync(prompt, conversation.inbox.provedor)
            
            # A resposta já é um dicionário
            if isinstance(ai_response, dict):
                if 'resposta' in ai_response:
                    # Extrair JSON da resposta
                    try:
                        import json
                        analysis = json.loads(ai_response['resposta'])
                    except:
                        # Fallback se não conseguir parsear JSON
                        analysis = {
                            'has_potential': 'interesse' in ai_response['resposta'].lower() if isinstance(ai_response['resposta'], str) else False,
                            'reason': 'Análise automática',
                            'suggested_approach': 'Contatar cliente'
                        }
                else:
                    analysis = ai_response
            else:
                # Se for string, tentar extrair JSON
                try:
                    import json
                    analysis = json.loads(ai_response)
                except:
                    # Fallback para análise simples
                    analysis = {
                        'has_potential': 'interesse' in ai_response.lower() if isinstance(ai_response, str) else False,
                        'reason': 'Análise automática',
                        'suggested_approach': 'Contatar cliente'
                    }
            
            return analysis
        except Exception as e:
            logger.error(f"Erro ao analisar conversa {conversation.id}: {e}")
            return {'has_potential': False, 'reason': f'Erro na análise: {str(e)}'}
    
    def generate_recovery_message(self, conversation_analysis: Dict, contact_name: str, provider_id: int) -> str:
        """
        Gera mensagem personalizada para recuperação de venda
        
        Args:
            conversation_analysis: Análise da conversa
            contact_name: Nome do contato
            
        Returns:
            Mensagem personalizada para recuperação
        """
        try:
            barriers = conversation_analysis.get('barriers', [])
            interest_level = conversation_analysis.get('interest_level', 'medio')
            suggested_approach = conversation_analysis.get('suggested_approach', '')
            
            # Prompt para gerar mensagem de recuperação
            prompt = f"""
            Gere uma mensagem personalizada para recuperar uma venda de internet.
            
            CONTEXTO:
            - Nome do cliente: {contact_name}
            - Nível de interesse: {interest_level}
            - Barreiras identificadas: {', '.join(barriers) if barriers else 'nenhuma'}
            - Abordagem sugerida: {suggested_approach}
            
            DIRETRIZES:
            1. Seja cordial e profissional
            2. Mencione que você viu o interesse do cliente
            3. Aborde as barreiras identificadas
            4. Ofereça soluções ou alternativas
            5. Seja direto mas não invasivo
            6. Máximo 200 caracteres
            
            Gere apenas a mensagem, sem aspas ou formatação.
            """
            
            # Usar o provedor do primeiro candidato (assumindo que todos são do mesmo provedor)
            # Por enquanto, vamos usar um provedor padrão ou implementar lógica para obter o provedor
            from core.models import Provedor
            provider = Provedor.objects.get(id=provider_id)
            message = self.openai_service.generate_response_sync(prompt, provider)
            
            # Se a resposta for um dicionário, extrair a mensagem
            if isinstance(message, dict) and 'resposta' in message:
                return message['resposta'].strip()
            elif isinstance(message, str):
                return message.strip()
            else:
                return f"Olá {contact_name}! Vi que você demonstrou interesse em nossos planos de internet. Gostaria de conversar sobre as opções disponíveis?"
            
        except Exception as e:
            logger.error(f"Erro ao gerar mensagem de recuperação: {e}")
            return f"Olá {contact_name}! Vi que você demonstrou interesse em nossos planos de internet. Gostaria de conversar sobre as opções disponíveis?"
    
    def send_recovery_message(self, contact_phone: str, message: str, provider_id: int) -> bool:
        """
        Envia mensagem de recuperação para o cliente
        
        Args:
            contact_phone: Telefone do cliente
            message: Mensagem de recuperação
            provider_id: ID do provedor
            
        Returns:
            True se enviada com sucesso
        """
        try:
            from integrations.models import WhatsAppIntegration
            from core.models import Provedor
            
            # Buscar integração WhatsApp do provedor
            provedor = Provedor.objects.get(id=provider_id)
            whatsapp_integration = WhatsAppIntegration.objects.filter(
                provedor=provedor
            ).first()
            
            if not whatsapp_integration:
                logger.error(f"Nenhuma integração WhatsApp encontrada para o provedor {provider_id}")
                return False
            
            # Limpar número do telefone
            phone_number = contact_phone.replace('@s.whatsapp.net', '').replace('@c.us', '')
            
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
            
            if result:
                logger.info(f"Mensagem de recuperação enviada para {contact_phone}: {message}")
                return True
            else:
                logger.error(f"Falha ao enviar mensagem de recuperação para {contact_phone}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de recuperação para {contact_phone}: {e}")
            return False
    
    def update_recovery_status_from_conversation(self, conversation_id: int, customer_message: str) -> bool:
        """
        Atualiza o status de recuperação baseado na resposta do cliente
        
        Args:
            conversation_id: ID da conversa
            customer_message: Mensagem do cliente
            
        Returns:
            True se o status foi atualizado
        """
        try:
            # Buscar tentativas de recuperação para esta conversa
            attempts = RecoveryAttempt.objects.filter(
                conversation_id=conversation_id,
                status='sent'  # Apenas tentativas enviadas
            ).order_by('-sent_at')
            
            if not attempts.exists():
                return False
            
            # Analisar se a mensagem indica interesse em contratar
            positive_keywords = [
                'contratar', 'contrato', 'aceito', 'sim', 'quero', 'vou contratar',
                'interessado', 'dados', 'endereço', 'instalação', 'quando',
                'preço', 'valor', 'pagamento', 'cartão', 'pix'
            ]
            
            message_lower = customer_message.lower()
            has_positive_response = any(keyword in message_lower for keyword in positive_keywords)
            
            if has_positive_response:
                # Atualizar a tentativa mais recente para 'recovered'
                latest_attempt = attempts.first()
                latest_attempt.status = 'recovered'
                latest_attempt.save()
                
                logger.info(f"Status de recuperação atualizado para 'recovered' na conversa {conversation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status de recuperação: {e}")
            return False
    
    def process_recovery_campaign(self, provider_id: int, days_back: int = 7) -> Dict:
        """
        Processa campanha completa de recuperação
        
        Args:
            provider_id: ID do provedor
            days_back: Quantos dias analisar
            
        Returns:
            Relatório da campanha
        """
        try:
            # Buscar configurações do provedor
            settings = self.get_provider_settings(provider_id)
            
            # Verificar se o recuperador está ativado
            if not settings.enabled:
                logger.info(f"Recuperador desativado para provedor {provider_id}")
                return {
                    'status': 'disabled',
                    'message': 'Recuperador está desativado para este provedor',
                    'total_analyzed': 0,
                    'messages_sent': 0,
                    'successful_sends': 0,
                    'failed_sends': 0,
                    'details': []
                }
            
            # Analisar conversas
            candidates = self.analyze_provider_conversations(provider_id, days_back)
            
            results = {
                'total_analyzed': len(candidates),
                'messages_sent': 0,
                'successful_sends': 0,
                'failed_sends': 0,
                'details': []
            }
            
            for candidate in candidates:
                try:
                    # Verificar se já existe tentativa para esta conversa
                    existing_attempt = RecoveryAttempt.objects.filter(
                        conversation_id=candidate['conversation_id']
                    ).first()
                    
                    # Verificar se já atingiu o máximo de tentativas
                    if existing_attempt and existing_attempt.attempt_number >= settings.max_attempts:
                        logger.info(f"Conversa {candidate['conversation_id']} já atingiu máximo de tentativas ({settings.max_attempts})")
                        continue
                    
                    # Gerar mensagem personalizada
                    message = self.generate_recovery_message(
                        candidate['analysis'], 
                        candidate['contact_name'],
                        provider_id
                    )
                    
                    # Criar registro de tentativa
                    attempt = RecoveryAttempt.objects.create(
                        conversation_id=candidate['conversation_id'],
                        attempt_number=existing_attempt.attempt_number + 1 if existing_attempt else 1,
                        message_sent=message,
                        status='pending',
                        additional_attributes={
                            'analysis_data': candidate['analysis'],
                            'recovery_reason': candidate['recovery_reason'],
                            'interest_level': candidate['analysis'].get('interest_level', 'medio'),
                            'barriers': candidate['analysis'].get('barriers', [])
                        }
                    )
                    
                    # Enviar mensagem
                    success = self.send_recovery_message(
                        candidate['contact_phone'],
                        message,
                        provider_id
                    )
                    
                    if success:
                        attempt.status = 'sent'
                        attempt.sent_at = timezone.now()
                        attempt.save()
                        
                        results['successful_sends'] += 1
                        results['messages_sent'] += 1
                    else:
                        attempt.status = 'failed'
                        attempt.save()
                        results['failed_sends'] += 1
                    
                    results['details'].append({
                        'contact': candidate['contact_name'],
                        'phone': candidate['contact_phone'],
                        'message_sent': success,
                        'recovery_reason': candidate['recovery_reason'],
                        'attempt_id': attempt.id
                    })
                    
                except Exception as e:
                    logger.error(f"Erro ao processar candidato {candidate['contact_name']}: {e}")
                    results['failed_sends'] += 1
            
            logger.info(f"Campanha de recuperação concluída para provedor {provider_id}: {results['successful_sends']} mensagens enviadas")
            return results
            
        except Exception as e:
            logger.error(f"Erro na campanha de recuperação para provedor {provider_id}: {e}")
            return {
                'total_analyzed': 0,
                'messages_sent': 0,
                'successful_sends': 0,
                'failed_sends': 0,
                'error': str(e)
            }
