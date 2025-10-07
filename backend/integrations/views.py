from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import models
from core.models import CompanyUser
from .models import TelegramIntegration, EmailIntegration, WhatsAppIntegration, WebchatIntegration
from .serializers import (
    TelegramIntegrationSerializer, EmailIntegrationSerializer,
    WhatsAppIntegrationSerializer, WebchatIntegrationSerializer
)
from .telegram_service import telegram_manager
from .email_service import email_manager
import asyncio
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import tempfile
import traceback
from conversations.models import Contact, Conversation, Message, Inbox
from core.models import Company
from django.utils import timezone
from core.openai_service import openai_service
from core.models import Provedor
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import traceback
import time
import random
import subprocess
import os
import logging
import django

logger = logging.getLogger(__name__)
from django.conf import settings
from datetime import datetime, timedelta


def process_sent_message(data, msg_data, chatid_full, clean_instance, uazapi_url, uazapi_token):
    """
    Processa mensagens enviadas pelo sistema para salvar external_id
    """
    try:
        print(f"DEBUG: Processando mensagem enviada - ID: {msg_data.get('id')}, messageid: {msg_data.get('messageid')}")
        
        # Extrair external_id da mensagem enviada
        external_id = msg_data.get('id') or msg_data.get('messageid')
        print(f"DEBUG: External ID da mensagem enviada: {external_id}")
        
        if not external_id:
            print("DEBUG: Mensagem enviada sem external_id, ignorando")
            return JsonResponse({'status': 'ignored', 'reason': 'no external_id'}, status=200)
        
        # Buscar conversa existente
        phone = chatid_full.replace('@s.whatsapp.net', '').replace('@c.us', '')
        
        # Buscar contato
        contact = Contact.objects.filter(phone=phone).first()
        if not contact:
            print(f"DEBUG: Contato não encontrado para mensagem enviada: {phone}")
            return JsonResponse({'status': 'ignored', 'reason': 'contact not found'}, status=200)
        
        # Buscar conversa
        conversation = Conversation.objects.filter(contact=contact).first()
        if not conversation:
            print(f"DEBUG: Conversa não encontrada para mensagem enviada: {contact.id}")
            return JsonResponse({'status': 'ignored', 'reason': 'conversation not found'}, status=200)
        
        # Buscar mensagem mais recente da conversa (provavelmente a que acabou de ser enviada)
        recent_message = Message.objects.filter(
            conversation=conversation,
            is_from_customer=False
        ).order_by('-created_at').first()
        
        if recent_message:
            # Atualizar external_id na mensagem
            recent_message.external_id = external_id
            recent_message.save()
            
            print(f"DEBUG: External ID salvo na mensagem {recent_message.id}: {external_id}")
            return JsonResponse({'status': 'processed', 'external_id': external_id}, status=200)
        else:
            print("DEBUG: Mensagem recente não encontrada para atualizar external_id")
            return JsonResponse({'status': 'ignored', 'reason': 'recent message not found'}, status=200)
            
    except Exception as e:
        print(f"DEBUG: Erro ao processar mensagem enviada: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def verify_and_normalize_number(chatid, uazapi_url, uazapi_token):
    """
    Verifica e normaliza um número usando o endpoint /chat/check da Uazapi
    """
    if not chatid or not uazapi_url or not uazapi_token:
        return chatid
    
    try:
        # Limpar o número para verificação
        clean_number = chatid.replace('@s.whatsapp.net', '').replace('@c.us', '')
        
        # Construir URL do endpoint /chat/check
        check_url = uazapi_url.replace('/send/text', '/chat/check')
        
        # Payload para verificação
        payload = {
            'numbers': [clean_number]
        }
        
        print(f"DEBUG: Verificando número {clean_number} via /chat/check")
        
        # Fazer requisição para verificar o número
        response = requests.post(
            check_url,
            headers={
                'token': uazapi_token,
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG: Resposta /chat/check: {result}")
            
            # Verificar se o número foi encontrado
            if result and isinstance(result, list) and len(result) > 0:
                number_info = result[0]
                
                # Se o número foi verificado, usar o jid retornado
                if number_info.get('isInWhatsapp', False):
                    verified_jid = number_info.get('jid', '')
                    if verified_jid:
                        print(f"DEBUG: Número verificado e normalizado: {verified_jid}")
                        return verified_jid
                    else:
                        print(f"DEBUG: Número {clean_number} encontrado mas sem jid válido")
                else:
                    print(f"DEBUG: Número {clean_number} não encontrado no WhatsApp")
            else:
                print(f"DEBUG: Resposta inválida do /chat/check: {result}")
        else:
            print(f"DEBUG: Erro na verificação do número: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"DEBUG: Erro ao verificar número: {e}")
    
    # Se não conseguir verificar, retornar o número original
    return chatid


class TelegramIntegrationViewSet(viewsets.ModelViewSet):
    queryset = TelegramIntegration.objects.all()
    serializer_class = TelegramIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'superadmin':
            return TelegramIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                return TelegramIntegration.objects.filter(provedor__in=provedores)
            return TelegramIntegration.objects.none()
    
    @action(detail=True, methods=['post'])
    def connect(self, request, pk=None):
        """Conectar integração Telegram"""
        integration = self.get_object()
        
        try:
            # Executar conexão de forma assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(
                telegram_manager.start_integration(integration.id)
            )
            
            if success:
                return Response({'status': 'connected'})
            else:
                return Response(
                    {'error': 'Failed to connect'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Desconectar integração Telegram"""
        integration = self.get_object()
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(
                telegram_manager.stop_integration(integration.id)
            )
            
            return Response({'status': 'disconnected'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Enviar mensagem via Telegram"""
        integration = self.get_object()
        chat_id = request.data.get('chat_id')
        content = request.data.get('content')
        reply_to_message_id = request.data.get('reply_to_message_id')
        
        if not chat_id or not content:
            return Response(
                {'error': 'chat_id and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if integration.id in telegram_manager.services:
                service = telegram_manager.services[integration.id]
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success = loop.run_until_complete(
                    service.send_message(chat_id, content, reply_to_message_id)
                )
                
                if success:
                    return Response({'status': 'message sent'})
                else:
                    return Response(
                        {'error': 'Failed to send message'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Integration not connected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        user = request.user
        if user.user_type == 'superadmin':
            integrations = TelegramIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                integrations = TelegramIntegration.objects.filter(provedor__in=provedores)
            else:
                integrations = TelegramIntegration.objects.none()
        status_data = []
        for integration in integrations:
            status_data.append({
                'id': integration.id,
                'provedor': integration.provedor.nome,
                'phone_number': integration.phone_number,
                'is_active': integration.is_active,
                'is_connected': integration.is_connected,
                'is_running': integration.id in telegram_manager.services
            })
        return Response(status_data)


class EmailIntegrationViewSet(viewsets.ModelViewSet):
    queryset = EmailIntegration.objects.all()
    serializer_class = EmailIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'superadmin':
            return EmailIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                return EmailIntegration.objects.filter(provedor__in=provedores)
            return EmailIntegration.objects.none()
    

    
    @action(detail=True, methods=['post'])
    def start_monitoring(self, request, pk=None):
        """Iniciar monitoramento de e-mails"""
        integration = self.get_object()
        
        try:
            email_manager.start_integration(integration.id)
            return Response({'status': 'monitoring started'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop_monitoring(self, request, pk=None):
        """Parar monitoramento de e-mails"""
        integration = self.get_object()
        
        try:
            email_manager.stop_integration(integration.id)
            return Response({'status': 'monitoring stopped'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Enviar e-mail"""
        integration = self.get_object()
        to_email = request.data.get('to_email')
        subject = request.data.get('subject')
        content = request.data.get('content')
        reply_to_message_id = request.data.get('reply_to_message_id')
        
        if not to_email or not subject or not content:
            return Response(
                {'error': 'to_email, subject and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if integration.id in email_manager.services:
                service = email_manager.services[integration.id]
                success = service.send_email(to_email, subject, content, reply_to_message_id)
                
                if success:
                    return Response({'status': 'email sent'})
                else:
                    return Response(
                        {'error': 'Failed to send email'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Integration not running'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        user = request.user
        if user.user_type == 'superadmin':
            integrations = EmailIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                integrations = EmailIntegration.objects.filter(provedor__in=provedores)
            else:
                integrations = EmailIntegration.objects.none()
        status_data = []
        for integration in integrations:
            status_data.append({
                'id': integration.id,
                'name': integration.name,
                'email': integration.email,
                'provider': integration.get_provider_display(),
                'provedor': integration.provedor.nome,
                'is_active': integration.is_active,
                'is_connected': integration.is_connected,
                'is_running': integration.id in email_manager.services
            })
        return Response(status_data)


class WhatsAppIntegrationViewSet(viewsets.ModelViewSet):
    queryset = WhatsAppIntegration.objects.all()
    serializer_class = WhatsAppIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'superadmin':
            return WhatsAppIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                return WhatsAppIntegration.objects.filter(provedor__in=provedores)
            return WhatsAppIntegration.objects.none()


class WebchatIntegrationViewSet(viewsets.ModelViewSet):
    queryset = WebchatIntegration.objects.all()
    serializer_class = WebchatIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'superadmin':
            return WebchatIntegration.objects.all()
        else:
            provedores = Provedor.objects.filter(admins=user)
            if provedores.exists():
                return WebchatIntegration.objects.filter(provedor__in=provedores)
            return WebchatIntegration.objects.none()
    
    @action(detail=True, methods=['get'])
    def widget_script(self, request, pk=None):
        """Gerar script do widget de chat"""
        integration = self.get_object()
        
        script = f"""
        <script>
        (function() {{
            var chatWidget = document.createElement('div');
            chatWidget.id = 'niochat-widget';
            chatWidget.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background-color: {integration.widget_color};
                border-radius: 50%;
                cursor: pointer;
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
            `;
            chatWidget.innerHTML = '💬';
            
            chatWidget.onclick = function() {{
                // Abrir chat
                console.log('Chat widget clicked');
            }};
            
            document.body.appendChild(chatWidget);
        }})();
        </script>
        """
        
        return Response({
            'script': script,
            'widget_color': integration.widget_color,
            'welcome_message': integration.welcome_message
        })


@csrf_exempt
def evolution_webhook(request):
    if request.method == 'POST':
        try:
            print('Webhook recebido:', request.body)
            data = json.loads(request.body)
            event = data.get('event')
            msg_data = data.get('data', {})
            phone = msg_data.get('chatid') or msg_data.get('sender') or msg_data.get('key', {}).get('senderPn')
            content = msg_data.get('message', {}).get('conversation')
            instance = data.get('instance')
            
            # Buscar provedor correto baseado na instância
            from core.models import Provedor
            from integrations.models import WhatsAppIntegration
            
            # Tentar encontrar provedor pela integração WhatsApp
            whatsapp_integration = WhatsAppIntegration.objects.filter(
                instance_name=instance
            ).first()
            
            if whatsapp_integration:
                provedor = whatsapp_integration.provedor
            else:
                # Fallback: usar o primeiro provedor se não encontrar pela instância
                provedor = Provedor.objects.first()
                print(f"Provedor não encontrado para instância {instance}, usando primeiro provedor: {provedor.nome if provedor else 'Nenhum'}")
            
            if not provedor:
                return JsonResponse({'error': 'Nenhum provedor encontrado'}, status=400)
            
# Verificação de status removida - campo não existe mais
            
            # 2. Buscar ou criar contato
            contact, created = Contact.objects.get_or_create(
                phone=phone,
                provedor=provedor,
                defaults={
                    'name': msg_data.get('pushName') or phone,
                    'additional_attributes': {
                        'evolution_instance': instance,
                        'evolution_event': event
                    }
                }
            )
            
            # Atualizar dados do contato se necessário
            nome_evo = msg_data.get('pushName')
            avatar_evo = msg_data.get('avatar')
            updated = False
            
            if nome_evo and contact.name != nome_evo:
                contact.name = nome_evo
                updated = True
                
            if avatar_evo and contact.avatar != avatar_evo:
                contact.avatar = avatar_evo
                updated = True
            
            # Se não tem avatar, tentar buscar a foto do perfil automaticamente
            if not avatar_evo and not contact.avatar:
                try:
                    from .utils import update_contact_profile_picture
                    if update_contact_profile_picture(contact, instance, 'evolution'):
                        updated = True
                except Exception as e:
                    print(f"Erro ao buscar foto do perfil: {e}")
                
            if updated:
                contact.save()
                print(f"Contato atualizado: {contact.name} ({contact.phone})")
            
            if created:
                print(f"Novo contato criado: {contact.name} ({contact.phone}) para provedor {provedor.nome}")
            
            # 3. Buscar ou criar inbox do WhatsApp
            inbox, inbox_created = Inbox.objects.get_or_create(
                name=f'WhatsApp {instance}',
                channel_type='whatsapp',
                provedor=provedor,
                defaults={
                    'settings': {
                        'evolution_instance': instance,
                        'evolution_event': event
                    }
                }
            )
            
            if inbox_created:
                print(f"Nova inbox criada: {inbox.name} para provedor {provedor.nome}")
            
            # 4. Buscar ou criar conversa - CORREÇÃO: evitar duplicação por canal
            existing_conversation = Conversation.objects.filter(
                contact=contact,
                inbox__channel_type='whatsapp'  # Buscar por canal, não por inbox específica
            ).first()
            
            if existing_conversation:
                # Usar conversa existente, mas atualizar inbox se necessário
                conversation = existing_conversation
                if conversation.inbox != inbox:
                    conversation.inbox = inbox
                    conversation.save()
                    print(f"Conversa {conversation.id} atualizada para inbox {inbox.name}")
                conv_created = False
            else:
                # Criar nova conversa
                conversation = Conversation.objects.create(
                    contact=contact,
                    inbox=inbox,
                    status='snoozed',
                    priority='medium',
                    additional_attributes={
                        'evolution_instance': instance,
                        'evolution_event': event
                    }
                )
                conv_created = True
                print(f"Nova conversa criada: {conversation.id} para contato {contact.name}")
            
            # Se a conversa já existia, preservar atribuição se houver agente
            if not conv_created:
                # Se não tem agente atribuído, colocar como snoozed
                if conversation.assignee is None:
                    conversation.status = 'snoozed'
                    conversation.save()
                # Se tem agente atribuído, manter como 'open' e preservar agente
                elif conversation.status != 'open':
                    conversation.status = 'open'
                    conversation.save()
                    print(f"Conversa mantida atribuída ao agente {conversation.assignee.username}")
            
            # 5. Salvar mensagem recebida - VERIFICAR DUPLICATA
            # Verificar se já existe uma mensagem com o mesmo conteúdo nos últimos 30 segundos
            recent_time = timezone.now() - timedelta(seconds=30)
            existing_message = Message.objects.filter(
                conversation=conversation,
                content=content,
                created_at__gte=recent_time,
                is_from_customer=True
            ).first()
            
            if existing_message:
                content_preview = content[:30] if content else "sem conteúdo"
                print(f"  Mensagem duplicada ignorada: {content_preview}...")
                return JsonResponse({'status': 'ignored_duplicate'}, status=200)
            
            # Extrair external_id da mensagem
            external_id = msg_data.get('id') or msg_data.get('key', {}).get('id') or msg_data.get('messageid')
            
            # Preparar additional_attributes com external_id e informações de resposta
            additional_attrs = {}
            if external_id:
                additional_attrs['external_id'] = external_id
                print(f"DEBUG: External ID extraído: {external_id}")
            
            # Adicionar informações de mensagem respondida se existir
            # Verificar se há informações de resposta no msg_data
            quoted_message = msg_data.get('quotedMessage') or msg_data.get('quoted_message') or msg_data.get('reply_to')
            reply_to_message_id = None
            reply_to_content = None
            
            if quoted_message:
                if isinstance(quoted_message, dict):
                    reply_to_message_id = quoted_message.get('id') or quoted_message.get('messageId')
                    reply_to_content = quoted_message.get('text') or quoted_message.get('content')
                elif isinstance(quoted_message, str):
                    reply_to_message_id = quoted_message
                    reply_to_content = "Mensagem respondida"
            
            if reply_to_message_id:
                additional_attrs['reply_to_message_id'] = reply_to_message_id
                additional_attrs['reply_to_content'] = reply_to_content
                additional_attrs['is_reply'] = True
                print(f"DEBUG: Informações de resposta adicionadas ao additional_attributes")
            
            msg = Message.objects.create(
                conversation=conversation,
                message_type='incoming',
                content=content or '',
                is_from_customer=True,  # Garantir que mensagens do cliente sejam marcadas corretamente
                additional_attributes=additional_attrs,
                created_at=timezone.now()
            )
            
            print(f"DEBUG: Nova mensagem salva: {msg.id} - {content[:30]}...")
            
            # Processar possível resposta CSAT
            from conversations.csat_automation import CSATAutomationService
            try:
                csat_feedback = CSATAutomationService.process_csat_response(
                    content or '', conversation, contact
                )
                if csat_feedback:
                    print(f"DEBUG: CSAT feedback processado: {csat_feedback.id} - Rating: {csat_feedback.rating_value}")
                    # Se processou CSAT, não enviar para IA
                    return JsonResponse({'status': 'csat_processed'}, status=200)
            except Exception as csat_error:
                print(f"DEBUG: Erro ao processar CSAT: {csat_error}")
            
            # Determinar o tipo de mensagem para salvar no banco
            message_type = msg_data.get('messageType') or msg_data.get('type', 'text')
            db_message_type = message_type if message_type in ['audio', 'image', 'video', 'document', 'sticker', 'ptt', 'media'] else 'incoming'
            
            # SALVAR MENSAGEM DO CLIENTE NO REDIS
            try:
                from core.redis_memory_service import redis_memory_service
                redis_memory_service.add_message_to_conversation_sync(
                    provedor_id=provedor.id,
                    conversation_id=conversation.id,
                    sender='customer',
                    content=content or '',
                    message_type=db_message_type
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar mensagem do cliente no Redis: {e}")
            
            # Emitir evento WebSocket para mensagem recebida
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            from conversations.serializers import MessageSerializer
            async_to_sync(channel_layer.group_send)(
                f"conversation_{conversation.id}",
                {
                    "type": "chat_message",
                    "message": MessageSerializer(msg).data,
                    "sender": None,
                    "timestamp": msg.created_at.isoformat(),
                }
            )
            
            # Emitir evento para o dashboard (toda vez que chega mensagem nova)
            from conversations.serializers import ConversationSerializer
            async_to_sync(channel_layer.group_send)(
                "conversas_dashboard",
                {
                    "type": "dashboard_event",
                    "data": {
                        "action": "update_conversation",
                        "conversation": ConversationSerializer(conversation).data
                    }
                }
            )
            
            # 6. Acionar IA para resposta automática (apenas se não estiver atribuída E não for CSAT)
            should_call_ai = (
                conversation.assignee is None and 
                conversation.status != 'pending' and
                conversation.status != 'closed'  # Não acionar IA se conversa estiver fechada
            )
            
            # Verificar se há CSAT pendente para esta conversa
            from conversations.models import CSATRequest
            csat_pending = CSATRequest.objects.filter(
                conversation=conversation,
                status__in=['pending', 'sent']
            ).exists()
            
            if csat_pending:
                should_call_ai = False
                print(f"🤖 IA: Não acionada - CSAT pendente para conversa {conversation.id}")
            
            # Importar openai_service uma vez
            from core.openai_service import openai_service
            
            if should_call_ai:
                print(f"🤖 IA: Acionando IA para mensagem: {content[:50]}...")
                ia_result = openai_service.generate_response_sync(
                    mensagem=content,
                    provedor=provedor,
                    contexto={'conversation': conversation}
                )
            else:
                print(f"🤖 IA: Não acionada - Conversa atribuída ao agente {conversation.assignee.username if conversation.assignee else 'N/A'} ou em espera ou fechada")
                ia_result = {'success': False, 'motivo': 'Conversa atribuída, em espera ou fechada'}
            
            print(f"🤖 IA: Resultado: {ia_result}")
            resposta_ia = ia_result.get('resposta') if ia_result.get('success') else None
            
            # 7. Enviar resposta para Evolution (WhatsApp)
            evolution_url = f'https://evo.niochat.com.br/message/sendText/{instance}'
            evolution_apikey = '78be6d7e78e8be03ba5e3cbdf1443f1c'  # Trocar para variável de ambiente se necessário
            send_result = None
            
            if resposta_ia:
                print(f"DEBUG: Criando mensagem da IA - resposta_ia: {resposta_ia}")
                try:
                    send_resp = requests.post(
                        evolution_url,
                        headers={'apikey': evolution_apikey, 'Content-Type': 'application/json'},
                        json={
                            'number': msg_data.get('key', {}).get('remoteJid') or phone.replace('@s.whatsapp.net', '').replace('@lid', ''),
                            'text': resposta_ia,
                            'delay': 2000
                        },
                        timeout=10
                    )
                    send_result = send_resp.json() if send_resp.content else send_resp.status_code
                    
                    # Salvar mensagem outgoing - VERIFICAR DUPLICATA
                    # Verificar se já existe uma mensagem da IA com o mesmo conteúdo nos últimos 30 segundos
                    recent_time = django.utils.timezone.now() - timedelta(seconds=30)
                    existing_ia_message = Message.objects.filter(
                        conversation=conversation,
                        content=resposta_ia,
                        created_at__gte=recent_time,
                        is_from_customer=False
                    ).first()
                    
                    if existing_ia_message:
                        resposta_preview = str(resposta_ia)[:30] if resposta_ia else "sem resposta"
                        print(f"  Mensagem da IA duplicada ignorada: {resposta_preview}...")
                    else:
                        print(f"DEBUG: Salvando mensagem da IA com is_from_customer=False")
                        # Extrair external_id da resposta da IA se disponível
                        ia_external_id = None
                        if send_result and isinstance(send_result, dict):
                            ia_external_id = send_result.get('id') or send_result.get('message_id')
                        
                        # Preparar additional_attributes para mensagem da IA
                        ia_additional_attrs = {}
                        if ia_external_id:
                            ia_additional_attrs['external_id'] = ia_external_id
                            print(f"DEBUG: External ID da IA extraído: {ia_external_id}")
                        
                        msg_out = Message.objects.create(
                            conversation=conversation,
                            message_type='text',  # Corrigido para valor válido
                            content=resposta_ia,
                            is_from_customer=False,  # Corrigido para identificar como mensagem da IA
                            external_id=ia_external_id,  # Salvar external_id no campo correto
                            additional_attributes=ia_additional_attrs,
                            created_at=django.utils.timezone.now()
                        )
                        
                        print(f"DEBUG: Mensagem da IA criada com ID: {msg_out.id}, is_from_customer: {msg_out.is_from_customer}")
                        resposta_preview = resposta_ia[:30] if resposta_ia else "sem resposta"
                        resposta_preview = str(resposta_ia)[:30] if resposta_ia else "sem resposta"
                        print(f"DEBUG: Resposta IA enviada: {msg_out.id} - {resposta_preview}...")
                        
                        # SALVAR MENSAGEM DA IA NO REDIS
                        try:
                            from core.redis_memory_service import redis_memory_service
                            redis_memory_service.add_message_to_conversation_sync(
                                provedor_id=provedor.id,
                                conversation_id=conversation.id,
                                sender='ai',
                                content=resposta_ia,
                                message_type='text'
                            )
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem da IA no Redis: {e}")
                        
                        # Emitir evento WebSocket para mensagem enviada
                        async_to_sync(channel_layer.group_send)(
                            f"conversation_{conversation.id}",
                            {
                                "type": "chat_message",
                                "message": MessageSerializer(msg_out).data,
                                "sender": None,
                                "timestamp": msg_out.created_at.isoformat(),
                            }
                        )
                except Exception as e:
                    send_result = f'Erro ao enviar para Evolution: {str(e)}'
                    print(f"Erro ao enviar resposta IA: {e}")
            
            print('Mensagem salva:', msg.id)
            print('Resposta IA:', resposta_ia)
            print('Envio Evolution:', send_result)
            
            return JsonResponse({
                'status': 'ok', 
                'resposta_ia': resposta_ia, 
                'envio': send_result,
                'contact_created': created,
                'conversation_created': conv_created,
                'provedor': provedor.nome
            })
            
        except Exception as e:
            print(f"Erro no webhook: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)


@csrf_exempt
def webhook_evolution_uazapi(request):
    """Webhook para receber mensagens da Uazapi"""
    from datetime import datetime
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        event_type = data.get('event') or data.get('EventType') or data.get('type')
        msg_data = data.get('data') or data.get('message', {})
        
        # Extrair chatid corretamente
        chatid = msg_data.get('chatid', '')
        sender_lid = msg_data.get('sender_lid', '')
        
        # Verificar se o chatid é válido (não deve ser o número conectado)
        instance = data.get('instance') or data.get('owner')
        clean_instance = instance.replace('@s.whatsapp.net', '').replace('@c.us', '') if instance else ''
        clean_chatid = chatid.replace('@s.whatsapp.net', '').replace('@c.us', '') if chatid else ''
        
        print(f"DEBUG: clean_instance: {clean_instance}")
        print(f"DEBUG: clean_chatid: {clean_chatid}")
        
        if clean_chatid == clean_instance:
            print(f"DEBUG: Ignorando mensagem do próprio número conectado: {chatid}")
            return JsonResponse({'status': 'ignored', 'reason': 'message from connected number'}, status=200)
        
        # Buscar provedor e credenciais ANTES da verificação de números
        from core.models import Provedor
        
        print(f"DEBUG: Buscando provedor para instance: {instance}")
        
        # Buscar provedor CORRETO baseado na instance/owner
        # A instance/owner deve corresponder ao número conectado do provedor
        provedor = None
        
        # Buscar todos os provedores com credenciais da Uazapi
        provedores = Provedor.objects.filter(
            integracoes_externas__whatsapp_token__isnull=False
        )
        
        print(f"DEBUG: Provedores encontrados com credenciais: {[p.nome for p in provedores]}")
        
        # Buscar o provedor correto baseado na instance
        for p in provedores:
            # Verificar se a instance corresponde ao número conectado do provedor
            provedor_instance = p.integracoes_externas.get('whatsapp_instance')
            print(f"DEBUG: Comparando instance {clean_instance} com provedor {p.nome} (instance: {provedor_instance})")
            if provedor_instance and clean_instance == provedor_instance.replace('@s.whatsapp.net', '').replace('@c.us', ''):
                provedor = p
                print(f"DEBUG: Provedor CORRETO encontrado: {provedor.nome} (instance: {provedor_instance})")
                break
        
        # Se não encontrar por instance, tentar por token
        if not provedor:
            for p in provedores:
                uazapi_token = p.integracoes_externas.get('whatsapp_token')
                if uazapi_token and uazapi_token in str(data):
                    provedor = p
                    print(f"DEBUG: Provedor encontrado por token: {provedor.nome}")
                    break
        
        # Se ainda não encontrar, usar o primeiro (fallback)
        if not provedor:
            provedor = provedores.first()
            print(f"DEBUG: Usando provedor fallback: {provedor.nome}")
        
        if not provedor:
            print("DEBUG: Nenhum provedor com credenciais da Uazapi encontrado")
            return JsonResponse({'error': 'Nenhum provedor com credenciais da Uazapi encontrado'}, status=400)
        
        # Verificação de status removida - campo não existe mais
        
        print(f"DEBUG: Provedor final selecionado: {provedor.nome}")
        
        # Buscar token e url da UazAPI do provedor
        uazapi_token = provedor.integracoes_externas.get('whatsapp_token')
        uazapi_url = provedor.integracoes_externas.get('whatsapp_url')
        
        if not uazapi_token or not uazapi_url:
            print(" DEBUG: Token ou URL não configurados no provedor")
            return JsonResponse({'error': 'Token ou URL não configurados no provedor'}, status=400)
        
        # Sensitive data log removed for security
        print(f"DEBUG: URL do provedor: {uazapi_url}")
        
        # Verificar e normalizar o número usando /chat/check
        if chatid and uazapi_url and uazapi_token:
            print(f"DEBUG: Verificando número via /chat/check antes da normalização")
            verified_chatid = verify_and_normalize_number(chatid, uazapi_url, uazapi_token)
            if verified_chatid != chatid:
                print(f"DEBUG: Número verificado e corrigido: {chatid} -> {verified_chatid}")
                chatid = verified_chatid
            else:
                print(f"ℹ️ DEBUG: Número mantido como original: {chatid}")
        
        # Normalizar chatid usando a lógica do n8n
        if chatid and chatid.endswith('@s.whatsapp.net'):
            # Se termina com @s.whatsapp.net, pegar apenas o número
            chatid_clean = chatid.split('@')[0]
            chatid_full = chatid  # Manter o completo para envio
        else:
            # Se não termina com @s.whatsapp.net, adicionar
            chatid_clean = chatid
            chatid_full = f"{chatid}@s.whatsapp.net" if chatid else ''
        
        print(f"DEBUG: chatid_clean final: {chatid_clean}")
        print(f"DEBUG: chatid_full final: {chatid_full}")
        
        # Verificar se o chatid_clean é válido
        if not chatid_clean or chatid_clean == clean_instance:
            print(f"DEBUG: Ignorando chatid inválido: {chatid_clean}")
            return JsonResponse({'status': 'ignored', 'reason': 'invalid chatid'}, status=200)
        
        # Verificar se é uma mensagem enviada pelo sistema (fromMe: true)
        fromMe = msg_data.get('fromMe', False)
        if fromMe:
            print(f"DEBUG: Mensagem enviada pelo sistema detectada (fromMe: {fromMe})")
            # Processar mensagem enviada para salvar external_id
            return process_sent_message(data, msg_data, chatid_full, clean_instance, uazapi_url, uazapi_token)
        
        phone = chatid_full
        name = msg_data.get('pushName') or msg_data.get('senderName') or phone or 'Contato'
        instance = data.get('instance') or data.get('owner')

        # Extrair conteúdo da mensagem para a IA
        content = (
            msg_data.get('content') or
            msg_data.get('text') or
            msg_data.get('caption')
        )
        
        # Verificar se é uma mensagem respondida (reply) ANTES de converter content para string
        quoted_message = msg_data.get('quotedMessage') or msg_data.get('quoted_message') or msg_data.get('reply_to')
        reply_to_message_id = None
        reply_to_content = None
        
        # Verificar se há campo 'quoted' (novo formato)
        quoted_id = msg_data.get('quoted')
        if quoted_id:
            print(f"DEBUG: Campo 'quoted' encontrado: {quoted_id}")
            reply_to_message_id = quoted_id
        
        # Verificar se quotedMessage está dentro de content.contextInfo (novo formato)
        if not quoted_message and isinstance(content, dict):
            context_info = content.get('contextInfo', {})
            quoted_message = context_info.get('quotedMessage')
            if quoted_message:
                print(f"DEBUG: quotedMessage encontrado em content.contextInfo: {quoted_message}")
        
        if quoted_message:
            print(f"DEBUG: Mensagem respondida detectada: {quoted_message}")
            # Extrair informações da mensagem respondida
            if isinstance(quoted_message, dict):
                # Verificar se tem extendedTextMessage (novo formato)
                if 'extendedTextMessage' in quoted_message:
                    extended_msg = quoted_message['extendedTextMessage']
                    reply_to_content = extended_msg.get('text', 'Mensagem respondida')
                    if not reply_to_message_id:
                        reply_to_message_id = quoted_id or "ID_da_mensagem_respondida" # Fallback if quoted_id is also missing
                # Verificar se tem conversation (formato mais simples)
                elif 'conversation' in quoted_message:
                    reply_to_content = quoted_message.get('conversation', 'Mensagem respondida')
                    if not reply_to_message_id:
                        reply_to_message_id = quoted_id or "ID_da_mensagem_respondida"
                else:
                    reply_to_message_id = quoted_message.get('id') or quoted_message.get('messageId') or quoted_message.get('key', {}).get('id')
                    reply_to_content = quoted_message.get('text') or quoted_message.get('content') or quoted_message.get('caption')
            elif isinstance(quoted_message, str):
                reply_to_message_id = quoted_message
                reply_to_content = "Mensagem respondida"
            
            print(f"DEBUG: ID da mensagem respondida: {reply_to_message_id}")
            print(f"DEBUG: Conteúdo da mensagem respondida: {reply_to_content}")
        
        # Agora converter content para string se for um objeto
        print(f"🔍 DEBUG: Antes da conversão - content = {content} (tipo: {type(content)})")
        if isinstance(content, dict) and 'text' in content:
            content = content['text']
            print(f"DEBUG: Conteúdo extraído do objeto: {content}")
        print(f"🔍 DEBUG: Após conversão - content = {content} (tipo: {type(content)})")
        
        # Detectar tipo de mensagem
        message_type = msg_data.get('type') or msg_data.get('messageType') or 'text'
        media_type = msg_data.get('mediaType') or msg_data.get('media_type')
        
        # Verificar se é uma mensagem de áudio baseada no conteúdo
        is_audio_message = False
        is_from_customer = True  # Por padrão, mensagens são do cliente
        if isinstance(content, dict) and content.get('mimetype', '').startswith('audio/'):
            is_audio_message = True
            message_type = 'audio'
            print(f"DEBUG: ÁUDIO DETECTADO")
        else:
            print(f"DEBUG: Não é áudio")
        
        print(f"DEBUG: Tipo de mensagem: {message_type}")
        
        # Verificar se é uma reação
        if message_type == 'ReactionMessage' or message_type == 'reaction':
            print(f"DEBUG: REAÇÃO DETECTADA!")
            # Para reações, não criar nova mensagem, apenas atualizar a mensagem original
            reaction_emoji = content
            
            # Extrair o ID da mensagem original de diferentes campos
            reaction_id = None
            
            # Tentar diferentes campos para encontrar o ID da mensagem original
            if 'reaction' in msg_data:
                reaction_id = msg_data['reaction']
                print(f"DEBUG: Reaction ID do campo 'reaction': {reaction_id}")
            elif 'content' in msg_data and isinstance(msg_data['content'], dict):
                # Verificar se o content tem informações da mensagem original
                content_data = msg_data['content']
                if 'key' in content_data and 'ID' in content_data['key']:
                    reaction_id = content_data['key']['ID']
                    print(f"DEBUG: Reaction ID do content.key.ID: {reaction_id}")
            
            # Se ainda não encontrou, tentar buscar pela mensagem mais recente do cliente
            if not reaction_id:
                print(f"DEBUG: Reaction ID não encontrado, buscando mensagem mais recente do cliente")
                try:
                    # Buscar a mensagem mais recente do cliente na conversa
                    recent_message = Message.objects.filter(
                        conversation=conversation,
                        is_from_customer=True
                    ).order_by('-created_at').first()
                    
                    if recent_message:
                        reaction_id = recent_message.external_id
                        print(f"DEBUG: Usando mensagem mais recente como reação: {reaction_id}")
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar mensagem recente: {e}")
            
            # Se ainda não encontrou, tentar buscar por mensagens de áudio recentes
            if not reaction_id:
                print(f"DEBUG: Tentando buscar por mensagens de áudio recentes")
                try:
                    # Buscar mensagens de áudio recentes do cliente
                    audio_messages = Message.objects.filter(
                        conversation=conversation,
                        is_from_customer=True,
                        message_type__in=['audio', 'ptt']
                    ).order_by('-created_at')[:3]  # Últimas 3 mensagens de áudio
                    
                    for audio_msg in audio_messages:
                        print(f"DEBUG: Verificando mensagem de áudio: {audio_msg.external_id}")
                        # Verificar se o timestamp da reação é próximo ao da mensagem de áudio
                        reaction_timestamp = msg_data.get('messageTimestamp', 0)
                        message_timestamp = audio_msg.created_at.timestamp() * 1000  # Converter para milissegundos
                        
                        # Se a diferença for menor que 5 minutos (300000ms), usar esta mensagem
                        if abs(reaction_timestamp - message_timestamp) < 300000:
                            reaction_id = audio_msg.external_id
                            print(f"DEBUG: Encontrada mensagem de áudio próxima: {reaction_id}")
                            break
                            
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar mensagens de áudio: {e}")
            
            # Se ainda não encontrou, tentar buscar pelo ID da reação (campo 'reaction')
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pelo ID da reação: {msg_data.get('reaction')}")
                try:
                    reaction_target_id = msg_data.get('reaction')
                    if reaction_target_id:
                        print(f"DEBUG: Buscando mensagem com external_id contendo: {reaction_target_id}")
                        print(f"DEBUG: Conversa ID: {conversation.id}")
                        
                        # Buscar mensagem que contenha o ID da reação no external_id
                        original_message = Message.objects.filter(
                            conversation=conversation,
                            external_id__icontains=reaction_target_id
                        ).first()
                        
                        if original_message:
                            reaction_id = original_message.external_id
                            print(f"DEBUG: Mensagem original encontrada pelo ID da reação: {reaction_id}")
                        else:
                            print(f"DEBUG: Mensagem não encontrada pelo ID da reação")
                            # Listar todas as mensagens da conversa para debug
                            all_messages = Message.objects.filter(conversation=conversation).values('id', 'external_id', 'message_type', 'created_at')[:5]
                            print(f"DEBUG: Últimas 5 mensagens da conversa: {list(all_messages)}")
                            
                            # Tentar buscar em todas as conversas
                            print(f"DEBUG: Tentando buscar em todas as conversas...")
                            global_message = Message.objects.filter(
                                external_id__icontains=reaction_target_id
                            ).first()
                            
                            if global_message:
                                print(f"DEBUG: Mensagem encontrada em outra conversa: {global_message.id} - Conversa: {global_message.conversation.id}")
                                # Se encontrou em outra conversa, usar essa conversa
                                conversation = global_message.conversation
                                reaction_id = global_message.external_id
                                print(f"DEBUG: Usando conversa: {conversation.id}")
                            
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar pelo ID da reação: {e}")
            
            # Se ainda não encontrou, tentar buscar pelo messageid sem o prefixo
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pelo messageid sem prefixo: {msg_data.get('messageid')}")
                try:
                    # Buscar mensagem pelo messageid sem o prefixo
                    messageid = msg_data.get('messageid')
                    if messageid:
                        # Tentar buscar pelo messageid completo
                        original_message = Message.objects.get(external_id=messageid)
                        print(f"DEBUG: Mensagem original encontrada pelo messageid: {original_message.id}")
                        reaction_id = messageid
                    else:
                        print(f"DEBUG: Messageid não encontrado")
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar pelo messageid: {e}")
            
            # Se ainda não encontrou, tentar buscar pelo ID da reação
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pelo ID da reação: {msg_data.get('id')}")
                try:
                    # Buscar mensagem pelo ID da reação
                    reaction_message_id = msg_data.get('id')
                    if reaction_message_id:
                        # Tentar buscar pelo ID da reação
                        original_message = Message.objects.get(external_id=reaction_message_id)
                        print(f"DEBUG: Mensagem original encontrada pelo ID da reação: {original_message.id}")
                        reaction_id = reaction_message_id
                    else:
                        print(f"DEBUG: ID da reação não encontrado")
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar pelo ID da reação: {e}")
            
            # Se ainda não encontrou, tentar buscar por diferentes formatos de ID
            if not reaction_id:
                print(f"DEBUG: Tentando buscar por diferentes formatos de ID")
                try:
                    # Tentar buscar por ID sem prefixo
                    if 'ACEC0B4C35057C2EE3C83EF5F570C42F' in str(msg_data):
                        # Buscar por ID sem prefixo
                        messages = Message.objects.filter(
                            conversation=conversation,
                            external_id__icontains='ACEC0B4C35057C2EE3C83EF5F570C42F'
                        )
                        if messages.exists():
                            reaction_id = messages.first().external_id
                            print(f"DEBUG: Encontrado por ID parcial: {reaction_id}")
                    
                    # Se ainda não encontrou, buscar pela mensagem mais recente de áudio
                    if not reaction_id:
                        audio_message = Message.objects.filter(
                            conversation=conversation,
                            message_type__in=['audio', 'ptt']
                        ).order_by('-created_at').first()
                        
                        if audio_message:
                            reaction_id = audio_message.external_id
                            print(f"DEBUG: Usando mensagem de áudio mais recente: {reaction_id}")
                            
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar por diferentes formatos: {e}")
            
            # Se ainda não encontrou, tentar buscar pela mensagem mais recente
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pela mensagem mais recente")
                try:
                    # Buscar a mensagem mais recente na conversa
                    recent_message = Message.objects.filter(
                        conversation=conversation
                    ).order_by('-created_at').first()
                    
                    if recent_message:
                        reaction_id = recent_message.external_id
                        print(f"DEBUG: Usando mensagem mais recente como reação: {reaction_id}")
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar mensagem recente: {e}")
            
            # Se ainda não encontrou, tentar buscar pelo ID da reação com prefixo
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pelo ID da reação com prefixo")
                try:
                    # Buscar pelo ID da reação com prefixo
                    reaction_id_with_prefix = f"{msg_data.get('owner')}:{msg_data.get('reaction')}"
                    print(f"DEBUG: Tentando buscar pelo ID com prefixo: {reaction_id_with_prefix}")
                    
                    original_message = Message.objects.get(external_id=reaction_id_with_prefix)
                    print(f"DEBUG: Mensagem original encontrada pelo ID com prefixo: {original_message.id}")
                    reaction_id = reaction_id_with_prefix
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar pelo ID com prefixo: {e}")
            
            # Se ainda não encontrou, tentar buscar pelo ID da reação sem prefixo
            if not reaction_id:
                print(f"DEBUG: Tentando buscar pelo ID da reação sem prefixo")
                try:
                    # Buscar pelo ID da reação sem prefixo
                    reaction_id_without_prefix = msg_data.get('reaction')
                    print(f"DEBUG: Tentando buscar pelo ID sem prefixo: {reaction_id_without_prefix}")
                    
                    # Buscar mensagem que contenha o ID da reação (mais recente primeiro)
                    original_message = Message.objects.filter(
                        conversation=conversation,
                        external_id__icontains=reaction_id_without_prefix
                    ).order_by('-created_at').first()
                    
                    if original_message:
                        print(f"DEBUG: Mensagem original encontrada pelo ID sem prefixo: {original_message.id}")
                        reaction_id = original_message.external_id
                    else:
                        print(f"DEBUG: Mensagem não encontrada pelo ID sem prefixo")
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar pelo ID sem prefixo: {e}")
            
            if reaction_id:
                print(f"DEBUG: Procurando mensagem original para reação: {reaction_id}")
                try:
                    # Buscar mensagem original pelo external_id exato
                    original_message = Message.objects.filter(external_id=reaction_id).first()
                    
                    # Se não encontrou, tentar buscar por external_id que contenha o reaction_id
                    if not original_message:
                        print(f"DEBUG: Buscando por external_id que contenha: {reaction_id}")
                        original_message = Message.objects.filter(
                            external_id__icontains=reaction_id
                        ).first()
                    
                    # Se ainda não encontrou, tentar buscar em todas as conversas
                    if not original_message:
                        print(f"DEBUG: Buscando em todas as conversas...")
                        original_message = Message.objects.filter(
                            external_id__icontains=reaction_id
                        ).first()
                    
                    if original_message:
                        print(f"DEBUG: Mensagem original encontrada: {original_message.id} - Conversa: {original_message.conversation.id}")
                        # Usar a conversa da mensagem original
                        conversation = original_message.conversation
                        print(f"DEBUG: Usando conversa: {conversation.id}")
                    else:
                        print(f"DEBUG: Mensagem original não encontrada para reação: {reaction_id}")
                        # Listar todas as mensagens para debug
                        all_messages = Message.objects.filter(conversation=conversation).values('id', 'external_id', 'message_type', 'created_at')[:5]
                        print(f"DEBUG: Últimas 5 mensagens da conversa: {list(all_messages)}")
                        return
                    
                    # Atualizar a mensagem original com a reação
                    if not original_message.additional_attributes:
                        original_message.additional_attributes = {}
                    
                    # Adicionar reação aos atributos
                    if 'reactions' not in original_message.additional_attributes:
                        original_message.additional_attributes['reactions'] = []
                    
                    # Adicionar reações recebidas do cliente
                    if 'received_reactions' not in original_message.additional_attributes:
                        original_message.additional_attributes['received_reactions'] = []
                    
                    # Definir phone_number para reações
                    phone_number = chatid_clean
                    
                    # Verificar se já existe reação do mesmo usuário
                    user_reaction = None
                    for reaction in original_message.additional_attributes['reactions']:
                        if reaction.get('user_id') == phone_number:
                            user_reaction = reaction
                            break
                    
                    # Se a reação está vazia, remover a reação existente
                    if not reaction_emoji or reaction_emoji.strip() == "":
                        if user_reaction:
                            original_message.additional_attributes['reactions'].remove(user_reaction)
                            print(f"DEBUG: Reação removida do usuário: {phone_number}")
                        else:
                            print(f"DEBUG: Nenhuma reação encontrada para remover do usuário: {phone_number}")
                    else:
                        if user_reaction:
                            # Atualizar reação existente
                            user_reaction['emoji'] = reaction_emoji
                            user_reaction['timestamp'] = msg_data.get('messageTimestamp', 0)
                            print(f"DEBUG: Reação atualizada: {reaction_emoji}")
                        else:
                            # Adicionar nova reação
                            original_message.additional_attributes['reactions'].append({
                                'user_id': phone_number,
                                'emoji': reaction_emoji,
                                'timestamp': msg_data.get('messageTimestamp', 0)
                            })
                            print(f"DEBUG: Nova reação adicionada: {reaction_emoji}")
                    
                    # Gerenciar reações recebidas do cliente
                    if reaction_emoji and reaction_emoji.strip() != "":
                        # Verificar se já existe reação do cliente
                        existing_customer_reaction = None
                        for reaction in original_message.additional_attributes['received_reactions']:
                            if reaction.get('from_customer', False):
                                existing_customer_reaction = reaction
                                break
                        
                        if existing_customer_reaction:
                            # Atualizar reação existente do cliente
                            existing_customer_reaction['emoji'] = reaction_emoji
                            existing_customer_reaction['timestamp'] = timezone.now().isoformat()
                        else:
                            # Adicionar nova reação do cliente
                            original_message.additional_attributes['received_reactions'].append({
                                'emoji': reaction_emoji,
                                'timestamp': timezone.now().isoformat(),
                                'from_customer': True
                            })
                    else:
                        # Se a reação está vazia, limpar todas as reações recebidas do cliente
                        original_message.additional_attributes['received_reactions'] = [
                            reaction for reaction in original_message.additional_attributes['received_reactions']
                            if not reaction.get('from_customer', False)
                        ]
                    
                    original_message.save()
                    print(f"DEBUG: Reação salva na mensagem original: {reaction_emoji}")
                    
                    # Enviar notificação WebSocket para atualizar o frontend
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f'conversation_{conversation.id}',
                            {
                                'type': 'message_updated',
                                'action': 'reaction_updated',
                                'message_id': original_message.id,
                                'reaction_emoji': reaction_emoji
                            }
                        )
                        print(f"DEBUG: WebSocket enviado para conversa {conversation.id}")
                    
                    return JsonResponse({'status': 'reaction_processed'}, status=200)
                    
                except Message.DoesNotExist:
                    print(f"DEBUG: Mensagem original não encontrada para reação: {reaction_id}")
                    # Se não encontrar a mensagem original, ignorar a reação
                    print(f"DEBUG: Ignorando reação sem mensagem original")
                    return JsonResponse({'status': 'reaction_ignored'}, status=200)
                except Exception as e:
                    print(f"DEBUG: Erro ao processar reação: {e}")
                    # Se houver erro, ignorar a reação
                    print(f"DEBUG: Ignorando reação com erro")
                    return JsonResponse({'status': 'reaction_error'}, status=200)
            else:
                print(f"DEBUG: Nenhum ID de reação encontrado, ignorando reação")
                return JsonResponse({'status': 'reaction_ignored'}, status=200)
        
        # Log específico para áudio
        if (message_type == 'audio' or message_type == 'ptt' or 
            message_type == 'AudioMessage' or media_type == 'ptt' or media_type == 'audio' or
            is_audio_message):
            print(f"DEBUG: MENSAGEM DE ÁUDIO DETECTADA!")
        
        # Para mensagens de mídia, não usar o JSON bruto como conteúdo
        print(f"🔍 DEBUG: Antes do processamento de mídia - content = '{content}' (tipo: {type(content)})")
        if (message_type in ['audio', 'image', 'video', 'document', 'sticker', 'ptt', 'media'] or
            message_type in ['AudioMessage', 'ImageMessage', 'VideoMessage', 'DocumentMessage'] or
            media_type in ['ptt', 'audio', 'image', 'video', 'document', 'sticker'] or
            is_audio_message):
            
            # Se o conteúdo for um JSON (objeto), não usar como texto
            print(f"🔍 DEBUG: Verificando se content é JSON - content = {content} (tipo: {type(content)})")
            if isinstance(content, dict) or (isinstance(content, str) and content.startswith('{')):
                print(f"🔍 DEBUG: Content é JSON, definindo como None")
                content = None
                print(f"DEBUG: Conteúdo JSON detectado")
            else:
                print(f"🔍 DEBUG: Content não é JSON, mantendo como: {content}")
            
            # Definir conteúdo apropriado para cada tipo de mídia
            print(f"🔍 DEBUG: Verificando se content está vazio - content = '{content}'")
            if not content:
                print(f"🔍 DEBUG: Content está vazio, definindo conteúdo apropriado para mídia")
                if (message_type in ['audio', 'ptt', 'AudioMessage'] or 
                    media_type in ['ptt', 'audio'] or is_audio_message):
                    content = 'Mensagem de voz'
                elif message_type in ['image', 'ImageMessage'] or media_type == 'image':
                    content = 'Imagem'
                elif message_type in ['sticker', 'StickerMessage'] or media_type == 'sticker':
                    content = 'Figurinha'
                elif message_type in ['video', 'VideoMessage'] or media_type == 'video':
                    content = 'Vídeo'
                elif message_type in ['document', 'DocumentMessage'] or media_type == 'document':
                    # Preservar content original para processamento de PDF
                    original_content = content
                    content = 'Documento'
                    print(f"DEBUG: original_content preservado: {original_content}")
                else:
                    content = f'Mídia ({message_type})'
                print(f"DEBUG: Conteúdo definido para mídia: {content}")
            else:
                print(f"🔍 DEBUG: Content não está vazio, mantendo como: '{content}'")
        else:
            # Para mensagens de texto, se não houver conteúdo, usar placeholder
            print(f"🔍 DEBUG: Mensagem de texto - content = '{content}'")
            if not content:
                print(f"🔍 DEBUG: Content vazio para texto, definindo placeholder")
                content = 'Mensagem de texto'
            else:
                print(f"🔍 DEBUG: Content não vazio para texto, mantendo como: '{content}'")
        
        print(f"🔍 DEBUG: Após processamento de mídia - content = '{content}' (tipo: {type(content)})")
        
        # Log final do conteúdo antes de salvar
        print(f"DEBUG: Conteúdo final antes de salvar: '{content}' (tipo: {type(content)})")

        # Filtrar apenas eventos de mensagem
        mensagem_eventos = ['message', 'messages', 'message_received', 'incoming_message', 'mensagem', 'mensagens']
        delete_eventos = ['delete', 'deleted', 'message_delete', 'message_deleted', 'revoke', 'revoked', 'remove', 'removed']
        
        event_type_lower = str(event_type).lower()
        
        # Log completo do evento recebido para debug
        print(f"DEBUG: Evento completo recebido:")
        print(f"DEBUG: event_type: {event_type}")
        print(f"DEBUG: data: {data}")
        print(f"DEBUG: msg_data: {msg_data}")
        
        # Verificar se é um evento de exclusão
        if event_type_lower in delete_eventos:
            print(f"DEBUG: Evento de exclusão detectado: {event_type}")
            print(f"DEBUG: event_type_lower: {event_type_lower}")
            print(f"DEBUG: delete_eventos: {delete_eventos}")
            
            # Extrair ID da mensagem deletada de diferentes possíveis locais
            deleted_message_id = (
                msg_data.get('id') or msg_data.get('messageid') or 
                msg_data.get('key', {}).get('id') or
                msg_data.get('messageId') or
                msg_data.get('message_id') or
                data.get('id') or
                data.get('messageId') or
                data.get('message_id')
            )
            
            print(f"DEBUG: deleted_message_id extraído: {deleted_message_id}")
            
            if deleted_message_id:
                print(f"DEBUG: Mensagem deletada no WhatsApp: {deleted_message_id}")
                
                # Buscar a mensagem no banco de dados pelo external_id
                try:
                    message = Message.objects.get(external_id=deleted_message_id)
                    print(f"DEBUG: Mensagem encontrada por external_id: {message.id}")
                    
                    # Marcar como deletada
                    additional_attrs = message.additional_attributes or {}
                    additional_attrs['status'] = 'deleted'
                    additional_attrs['deleted_at'] = str(datetime.now())
                    additional_attrs['deleted_by'] = 'client'
                    message.additional_attributes = additional_attrs
                    message.save()
                    
                    print(f"DEBUG: Mensagem marcada como deletada: {message.id}")
                    
                    # Emitir evento WebSocket
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    from conversations.serializers import MessageSerializer
                    message_data = MessageSerializer(message).data
                    
                    async_to_sync(channel_layer.group_send)(
                        f"conversation_{message.conversation.id}",
                        {
                            "type": "chat_message",
                            "message": message_data,
                            "sender": None,
                            "timestamp": message.updated_at.isoformat(),
                        }
                    )
                    
                    return JsonResponse({'status': 'message_deleted'}, status=200)
                    
                except Message.DoesNotExist:
                    print(f"DEBUG: Mensagem não encontrada no banco: {deleted_message_id}")
                    # Tentar buscar por outros campos
                    try:
                        # Buscar por ID da mensagem
                        message = Message.objects.get(id=deleted_message_id)
                        print(f"DEBUG: Mensagem encontrada por ID: {message.id}")
                        
                        # Marcar como deletada
                        additional_attrs = message.additional_attributes or {}
                        additional_attrs['status'] = 'deleted'
                        additional_attrs['deleted_at'] = str(datetime.now())
                        additional_attrs['deleted_by'] = 'client'
                        message.additional_attributes = additional_attrs
                        message.save()
                        
                        print(f"DEBUG: Mensagem marcada como deletada: {message.id}")
                        
                        # Emitir evento WebSocket
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        channel_layer = get_channel_layer()
                        from conversations.serializers import MessageSerializer
                        message_data = MessageSerializer(message).data
                        
                        async_to_sync(channel_layer.group_send)(
                            f"conversation_{message.conversation.id}",
                            {
                                "type": "chat_message",
                                "message": message_data,
                                "sender": None,
                                "timestamp": message.updated_at.isoformat(),
                            }
                        )
                        
                        return JsonResponse({'status': 'message_deleted'}, status=200)
                        
                    except Message.DoesNotExist:
                        print(f"DEBUG: Mensagem não encontrada nem por external_id nem por ID: {deleted_message_id}")
                        return JsonResponse({'status': 'message_not_found'}, status=200)
            else:
                print(f"DEBUG: ID da mensagem deletada não encontrado")
                return JsonResponse({'status': 'no_message_id'}, status=200)
        else:
            print(f"DEBUG: Evento não é de exclusão. event_type_lower: {event_type_lower}")
            print(f"DEBUG: delete_eventos: {delete_eventos}")
            print(f"DEBUG: event_type_lower in delete_eventos: {event_type_lower in delete_eventos}")
        
        # Verificar se é um evento de mensagem normal
        if event_type_lower not in mensagem_eventos:
            # Ignorar eventos que não são de mensagem
            return JsonResponse({'status': 'ignored'}, status=200)

        # 4. Detectar se é mensagem da IA (enviada pelo próprio número conectado)
        sender = msg_data.get('sender') or msg_data.get('from') or ''
        is_ai_response = False
        sender_clean = ''
        if sender:
            sender_clean = sender.replace('@s.whatsapp.net', '').replace('@c.us', '')
            if sender_clean == clean_instance:
                is_ai_response = True
        print(f"DEBUG: sender: {sender} | sender_clean: {sender_clean} | clean_instance: {clean_instance} | is_ai_response: {is_ai_response}")
        if is_ai_response:
            print(f"DEBUG: Ignorando mensagem da IA: {content}")
            return JsonResponse({'status': 'ignored', 'reason': 'AI response message'}, status=200)

        # Não responder mensagens enviadas pelo próprio número do bot (exceto para áudio)
        bot_number = str(instance)
        chatid = msg_data.get('chatid', '')
        sender_lid = msg_data.get('sender_lid', '')
        
        # Verificar se a mensagem está sendo enviada para o número conectado
        is_sent_to_bot = False
        if bot_number:
            # Limpar números para comparação
            clean_bot_number = bot_number.replace('@s.whatsapp.net', '').replace('@c.us', '')
            clean_chatid = chatid.replace('@s.whatsapp.net', '').replace('@c.us', '') if chatid else ''
            clean_sender_lid = sender_lid.replace('@lid', '').replace('@c.us', '') if sender_lid else ''
            
            # Verificar se está sendo enviado para o bot
            if (clean_chatid == clean_bot_number) or (clean_sender_lid == clean_bot_number):
                is_sent_to_bot = True
                print(f"DEBUG: Mensagem sendo enviada para o número conectado ({bot_number}) - IGNORANDO")
                return JsonResponse({'status': 'ignored', 'reason': 'message sent to connected number'}, status=200)
        
        print(f"DEBUG: Mensagem não está sendo enviada para o número conectado - processando normalmente")

        # 2. Buscar ou criar contato
        # Extrair chatid e sender_lid da mensagem
        chatid = msg_data.get('chatid', '')
        sender_lid = msg_data.get('sender_lid', '')
        
        # Extrair nome e avatar
        nome_evo = msg_data.get('senderName') or msg_data.get('pushName') or msg_data.get('senderName')
        avatar_evo = msg_data.get('avatar')
        
        print(f"DEBUG: Nome extraído: {nome_evo}")
        print(f"DEBUG: Avatar extraído: {avatar_evo}")
        
        # Usar chatid_clean para o phone_number (evitar duplicação)
        phone_number = chatid_clean
        
        print(f"DEBUG: phone_number final: {phone_number}")
        print(f"DEBUG: provedor: {provedor}")
        
        # Buscar contato existente por phone (que agora é o chatid limpo)
        contact = None
        if phone_number:
            # Buscar por phone_number exato primeiro
            contact = Contact.objects.filter(phone=phone_number, provedor=provedor).first()
            print(f"DEBUG: Busca exata por phone_number '{phone_number}': {'Encontrado' if contact else 'Não encontrado'}")
            
            # Se não encontrou, buscar por números similares (variações de dígitos)
            if not contact:
                # Criar variações do número para busca
                phone_variations = [
                    phone_number,                    # número original
                    phone_number[1:],               # sem primeiro dígito  
                    phone_number[2:],               # sem dois primeiros dígitos
                    f"55{phone_number[2:]}",        # adicionar 55 
                    f"559{phone_number[3:]}",       # adicionar 559
                    f"5594{phone_number[4:]}",      # adicionar 5594
                ]
                
                # Buscar contatos que tenham números similares
                for variation in phone_variations:
                    if len(variation) >= 8:  # apenas variações válidas
                        contact = Contact.objects.filter(
                            phone__endswith=variation[-8:],  # últimos 8 dígitos
                            provedor=provedor
                        ).first()
                        if contact:
                            print(f"DEBUG: Contato encontrado com variação '{variation[-8:]}': {contact.name} (ID: {contact.id}, Phone: {contact.phone})")
                            break
                
                if not contact:
                    print(f"DEBUG: Busca flexível por phone similar: Não encontrado")
            
            # Se não encontrou, buscar por chatid nos additional_attributes
            if not contact:
                contact = Contact.objects.filter(
                    additional_attributes__chatid__icontains=phone_number,
                    provedor=provedor
                ).first()
                print(f"DEBUG: Busca por chatid nos additional_attributes: {'Encontrado' if contact else 'Não encontrado'}")
            
            # Se ainda não encontrou, buscar por sender_lid (apenas como fallback)
            if not contact and sender_lid:
                contact = Contact.objects.filter(
                    additional_attributes__sender_lid=sender_lid,
                    provedor=provedor
                ).first()
                print(f"DEBUG: Busca por sender_lid '{sender_lid}': {'Encontrado' if contact else 'Não encontrado'}")
        
        if contact:
            print(f"DEBUG: Contato existente encontrado: {contact.name} (ID: {contact.id})")
            # Atualizar contato existente
            updated = False
            if nome_evo and contact.name != nome_evo:
                contact.name = nome_evo
                updated = True
            if avatar_evo and contact.avatar != avatar_evo:
                contact.avatar = avatar_evo
                updated = True
            
            # Atualizar phone se mudou
            if phone_number and contact.phone != phone_number:
                contact.phone = phone_number
                updated = True
            
            # Atualizar additional_attributes se necessário
            if sender_lid and contact.additional_attributes.get('sender_lid') != sender_lid:
                contact.additional_attributes['sender_lid'] = sender_lid
                updated = True
            
            if updated:
                contact.save()
                print(f"DEBUG: Contato atualizado: {contact.name}")
                
            # Buscar foto do perfil sempre (novos e existentes)
            if chatid_clean and uazapi_token and uazapi_url:
                try:
                    # Construir URL para o endpoint /chat/details
                    base_url = uazapi_url.rstrip('/')
                    chat_details_url = f"{base_url}/chat/details"
                    
                    payload = {
                        'number': chatid_clean
                    }
                    
                    print(f"DEBUG: Buscando foto do perfil para contato existente: {chatid_clean}")
                    print(f"DEBUG: URL: {chat_details_url}")
                    # Sensitive data log removed for security
                    
                    import requests as http_requests
                    response = http_requests.post(
                        chat_details_url,
                        headers={
                            'token': uazapi_token,
                            'Content-Type': 'application/json'
                        },
                        json=payload,
                        timeout=10
                    )
                    
                    print(f"DEBUG: Status code: {response.status_code}")
                    
                    if response.status_code == 200:
                        chat_data = response.json()
                        print(f"DEBUG: Resposta /chat/details: {chat_data}")
                        
                        # Verificar se há foto do perfil (sempre atualizar)
                        if 'image' in chat_data and chat_data['image']:
                            contact.avatar = chat_data['image']
                            contact.save()
                            print(f"DEBUG: Foto do perfil atualizada: {contact.avatar}")
                        else:
                            print(f"DEBUG: Nenhuma foto do perfil encontrada")
                            
                        # Verificar se há nome verificado (sempre atualizar se diferente)
                        if 'wa_name' in chat_data and chat_data['wa_name'] and contact.name != chat_data['wa_name']:
                            contact.name = chat_data['wa_name']
                            contact.save()
                            print(f"DEBUG: Nome verificado atualizado: {contact.name}")
                        elif 'name' in chat_data and chat_data['name'] and contact.name != chat_data['name']:
                            contact.name = chat_data['name']
                            contact.save()
                            print(f"DEBUG: Nome atualizado: {contact.name}")
                            
                    else:
                        print(f"DEBUG: Erro ao buscar foto do perfil: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar foto do perfil: {e}")
                    print(f"DEBUG: Traceback: {traceback.format_exc()}")
        else:
            print(f"DEBUG: Criando novo contato para phone_number: {phone_number}")
            # Criar novo contato
            contact = Contact.objects.create(
                phone=phone_number or '',
                provedor=provedor,
                name=nome_evo or phone_number or 'Contato Desconhecido',
                additional_attributes={
                    'instance': instance,
                    'event': event_type,
                    'chatid': chatid_full,  # Salvar chatid completo nos additional_attributes
                    'sender_lid': sender_lid
                }
            )
            print(f"DEBUG: Novo contato criado: {contact.name} (ID: {contact.id})")
            
            # Buscar foto do perfil usando o endpoint /chat/details da Uazapi (sempre)
            if chatid_clean and uazapi_token and uazapi_url:
                try:
                    # Construir URL para o endpoint /chat/details
                    base_url = uazapi_url.rstrip('/')
                    chat_details_url = f"{base_url}/chat/details"
                    
                    payload = {
                        'number': chatid_clean
                    }
                    
                    print(f"DEBUG: Buscando foto do perfil para: {chatid_clean}")
                    print(f"DEBUG: URL: {chat_details_url}")
                    # Sensitive data log removed for security
                    
                    import requests as http_requests
                    response = http_requests.post(
                        chat_details_url,
                        headers={
                            'token': uazapi_token,
                            'Content-Type': 'application/json'
                        },
                        json=payload,
                        timeout=10
                    )
                    
                    print(f"DEBUG: Status code: {response.status_code}")
                    
                    if response.status_code == 200:
                        chat_data = response.json()
                        print(f"DEBUG: Resposta /chat/details: {chat_data}")
                        
                        # Verificar se há foto do perfil
                        if 'image' in chat_data and chat_data['image']:
                            contact.avatar = chat_data['image']
                            contact.save()
                            print(f"DEBUG: Foto do perfil obtida: {contact.avatar}")
                        else:
                            print(f"DEBUG: Nenhuma foto do perfil encontrada")
                            
                        # Verificar se há nome verificado
                        if 'wa_name' in chat_data and chat_data['wa_name']:
                            contact.name = chat_data['wa_name']
                            contact.save()
                            print(f"DEBUG: Nome verificado obtido: {contact.name}")
                        elif 'name' in chat_data and chat_data['name']:
                            contact.name = chat_data['name']
                            contact.save()
                            print(f"DEBUG: Nome obtido: {contact.name}")
                            
                    else:
                        print(f"DEBUG: Erro ao buscar foto do perfil: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"DEBUG: Erro ao buscar foto do perfil: {e}")
                    print(f"DEBUG: Traceback: {traceback.format_exc()}")

        # 3. Buscar ou criar inbox específica para esta instância
        inbox, _ = Inbox.objects.get_or_create(
            name=f'WhatsApp {instance}',
            channel_type='whatsapp',
            provedor=provedor,
            defaults={
                'additional_attributes': {
                    'instance': instance,
                    'channel_type': 'whatsapp'
                }
            }
        )
        
        # Buscar ou criar conversa - CORREÇÃO: evitar duplicação por canal
        print(f"DEBUG: Buscando conversa existente para contato {contact.id} ({contact.name})")
        existing_conversation = Conversation.objects.filter(
            contact=contact,
            inbox__channel_type='whatsapp'  # Buscar por canal, não por inbox específica
        ).first()
        
        if existing_conversation:
            # Usar conversa existente, mas atualizar inbox se necessário
            conversation = existing_conversation
            print(f"DEBUG: Conversa existente encontrada - ID: {conversation.id}")
            if conversation.inbox != inbox:
                conversation.inbox = inbox
                conversation.save()
                print(f"Conversa {conversation.id} atualizada para inbox {inbox.name}")
            conv_created = False
        else:
            # Criar nova conversa
            conversation = Conversation.objects.create(
                contact=contact,
                inbox=inbox,
                status='snoozed',
                additional_attributes={
                    'instance': instance,
                    'event': event_type
                }
            )
            conv_created = True
            print(f"DEBUG: Nova conversa criada: {conversation.id} para contato {contact.name} (ID: {contact.id})")
        
        # Se a conversa já existia, preservar atribuição se houver agente
        if not conv_created:
            # Se não tem agente atribuído, colocar como snoozed
            if conversation.assignee is None:
                conversation.status = 'snoozed'
                conversation.save()
            # Se tem agente atribuído E a conversa não está fechada, manter como 'open'
            elif conversation.status != 'open' and conversation.status != 'closed':
                conversation.status = 'open'
                conversation.save()
                print(f"DEBUG: Conversa mantida atribuída ao agente {conversation.assignee.username}")
            # Se a conversa está fechada, colocar como 'snoozed' para IA responder
            elif conversation.status == 'closed':
                conversation.status = 'snoozed'
                conversation.assignee = None  # Remover agente para IA responder
                conversation.save()
                print(f"DEBUG: Conversa {conversation.id} reaberta como 'snoozed' para IA responder")
        
        # 4. Extrair external_id da mensagem
        external_id = msg_data.get('id') or msg_data.get('key', {}).get('id') or msg_data.get('messageid')
        print(f"DEBUG: Tentando extrair external_id - id: {msg_data.get('id')}, key.id: {msg_data.get('key', {}).get('id')}, messageid: {msg_data.get('messageid')}")
        print(f"DEBUG: External ID final: {external_id}")
        
        # 5. Processar mídia se for mensagem de mídia
        additional_attrs = {}
        if external_id:
            additional_attrs['external_id'] = external_id
            print(f"DEBUG: External ID extraído no webhook Uazapi: {external_id}")
        
        file_url = None
        
        if (message_type in ['audio', 'image', 'video', 'document', 'sticker', 'ptt', 'media'] or
            message_type in ['AudioMessage', 'ImageMessage', 'VideoMessage', 'DocumentMessage'] or
            media_type in ['ptt', 'audio', 'image', 'video', 'document', 'sticker'] or
            is_audio_message):
            
            print(f"DEBUG: Processando mensagem de mídia - tipo: {message_type}, media_type: {media_type}")
            print(f"DEBUG: Condição de mídia ativada - message_type: {message_type}, media_type: {media_type}")
            
            # Tentar baixar o arquivo da Uazapi
            try:
                # Buscar URL de download da Uazapi
                download_url = None
                if uazapi_url and uazapi_token:
                    # Construir URL de download baseada na URL base
                    base_url = uazapi_url.replace('/send/text', '')
                    download_url = f"{base_url}/message/download"
                
                if download_url and uazapi_token:
                    # Baixar arquivo da Uazapi
                    import os
                    from django.conf import settings
                    import requests
                    
                    # Criar diretório para mídia
                    media_dir = os.path.join(settings.MEDIA_ROOT, 'messages', str(conversation.id))
                    os.makedirs(media_dir, exist_ok=True)
                    
                    # Determinar extensão e prefixo baseados no tipo de mídia
                    file_extension = '.mp3'  # Padrão para áudio
                    file_prefix = 'audio'
                    
                    if isinstance(content, dict) and content.get('mimetype'):
                        mimetype = content.get('mimetype')
                        if 'image' in mimetype:
                            file_extension = '.jpg'
                            file_prefix = 'image'
                        elif 'video' in mimetype:
                            file_extension = '.mp4'
                            file_prefix = 'video'
                        elif 'document' in mimetype or 'pdf' in mimetype:
                            file_extension = '.pdf'
                            file_prefix = 'document'
                        elif 'ogg' in mimetype:
                            file_extension = '.ogg'
                            file_prefix = 'audio'
                        elif 'opus' in mimetype:
                            file_extension = '.opus'
                            file_prefix = 'audio'
                        elif 'mp3' in mimetype:
                            file_extension = '.mp3'
                            file_prefix = 'audio'
                        elif 'wav' in mimetype:
                            file_extension = '.wav'
                            file_prefix = 'audio'
                        elif 'm4a' in mimetype:
                            file_extension = '.m4a'
                            file_prefix = 'audio'
                        print(f"DEBUG: Extensão determinada pelo mimetype: {file_extension}")
                    else:
                        # Determinar baseado no tipo de mensagem
                        if message_type == 'image':
                            file_extension = '.jpg'
                            file_prefix = 'image'
                        elif message_type == 'video':
                            file_extension = '.mp4'
                            file_prefix = 'video'
                        elif message_type == 'document':
                            file_extension = '.pdf'
                            file_prefix = 'document'
                        elif message_type == 'audio' or is_audio_message:
                            file_extension = '.mp3'
                            file_prefix = 'audio'
                        else:
                            file_extension = '.mp3'
                            file_prefix = 'media'
                    
                    # Para áudios, sempre usar .mp3 para garantir compatibilidade
                    if message_type == 'audio' or is_audio_message:
                        file_extension = '.mp3'
                        file_prefix = 'audio'
                        print(f"DEBUG: Forçando extensão .mp3 para compatibilidade")
                    
                    # Gerar nome do arquivo
                    import time
                    timestamp = int(time.time() * 1000)
                    filename = f"{file_prefix}_{timestamp}{file_extension}"
                    file_path = os.path.join(media_dir, filename)
                    
                    # Preparar payload para download conforme documentação da Uazapi
                    message_id = msg_data.get('id') or msg_data.get('key', {}).get('id') or msg_data.get('messageid')
                    if not message_id:
                        print(f"DEBUG: ID da mensagem não encontrado para download")
                        print(f"DEBUG: msg_data keys: {list(msg_data.keys())}")
                        print(f"DEBUG: msg_data: {msg_data}")
                    else:
                        download_payload = {
                            'id': message_id,
                            'return_base64': False,  # Queremos o arquivo, não base64
                            'return_link': True,     # Queremos a URL pública
                        }
                        
                        # Para áudios, especificar formato
                        if message_type == 'audio' or is_audio_message:
                            download_payload['generate_mp3'] = True
                            # Forçar conversão para MP3 para garantir compatibilidade
                            download_payload['mimetype'] = 'audio/mpeg'
                            download_payload['format'] = 'mp3'  # Adicionar formato explícito
                            print(f"DEBUG: Forçando conversão para MP3")
                        
                        print(f"DEBUG: Baixando arquivo da Uazapi")
                        
                        download_response = requests.post(
                            download_url,
                            headers={'token': uazapi_token, 'Content-Type': 'application/json'},
                            json=download_payload,
                            timeout=15  # Reduzir timeout
                        )
                        
                        if download_response.status_code == 200:
                            try:
                                response_data = download_response.json()
                                
                                # Verificar se temos fileURL na resposta
                                if 'fileURL' in response_data:
                                    file_url = response_data['fileURL']
                                    print(f"DEBUG: URL do arquivo obtida")
                                    
                                    # Preparar atributos adicionais (manter external_id existente)
                                    additional_attrs.update({
                                        'file_url': file_url,
                                        'file_name': filename,
                                        'message_type': message_type,
                                        'original_message_id': message_id,
                                        'mimetype': response_data.get('mimetype', ''),
                                        'uazapi_response': response_data
                                    })
                                    
                                    # Baixar arquivo de forma otimizada
                                    try:
                                        print(f"DEBUG: Baixando arquivo do UazAPI")
                                        
                                        # Baixar arquivo do UazAPI com timeout reduzido
                                        file_response = requests.get(file_url, timeout=15)
                                        
                                        if file_response.status_code == 200:
                                            # Salvar arquivo localmente
                                            with open(file_path, 'wb') as f:
                                                f.write(file_response.content)
                                            
                                            # Conversão otimizada para MP3
                                            if filename.endswith('.webm'):
                                                try:
                                                    import subprocess
                                                    mp3_path = file_path.replace('.webm', '.mp3')
                                                    mp3_filename = filename.replace('.webm', '.mp3')
                                                    
                                                    print(f"DEBUG: Convertendo WebM para MP3")
                                                    
                                                    # Converter usando ffmpeg com timeout
                                                    result = subprocess.run([
                                                        'ffmpeg', '-i', file_path, 
                                                        '-acodec', 'libmp3lame', 
                                                        '-ab', '128k', 
                                                        '-y', mp3_path
                                                    ], capture_output=True, text=True, timeout=30)
                                                    
                                                    if result.returncode == 0:
                                                        print(f"DEBUG: Conversão para MP3 bem-sucedida")
                                                        # Usar o arquivo MP3 em vez do WebM
                                                        file_path = mp3_path
                                                        filename = mp3_filename
                                                        additional_attrs['file_path'] = mp3_path
                                                        additional_attrs['file_size'] = os.path.getsize(mp3_path)
                                                        # Usar URL pública acessível
                                                        additional_attrs['local_file_url'] = f"/api/media/messages/{conversation.id}/{mp3_filename}/"
                                                        print(f"DEBUG: Arquivo MP3 criado")
                                                    else:
                                                        print(f"DEBUG: Erro na conversão para MP3")
                                                except subprocess.TimeoutExpired:
                                                    print(f"DEBUG: Timeout na conversão para MP3")
                                                except Exception as e:
                                                    print(f"DEBUG: Erro ao converter para MP3: {e}")
                                            else:
                                                additional_attrs['file_path'] = file_path
                                                additional_attrs['file_size'] = len(file_response.content)
                                                # Usar URL pública acessível
                                                additional_attrs['local_file_url'] = f"/api/media/messages/{conversation.id}/{filename}/"

                                            print(f"DEBUG: Arquivo baixado e salvo localmente")
                                        else:
                                            print(f"DEBUG: Erro ao baixar arquivo do UazAPI: {file_response.status_code}")
                                    except requests.Timeout:
                                        print(f"DEBUG: Timeout ao baixar arquivo")
                                    except Exception as e:
                                        print(f"DEBUG: Erro ao baixar arquivo: {e}")
                                else:
                                    print(f"DEBUG: fileURL não encontrada na resposta")
                            except Exception as e:
                                print(f"DEBUG: Erro ao processar resposta: {e}")
                        else:
                            print(f"DEBUG: Erro ao baixar arquivo da Uazapi: {download_response.status_code}")

            except Exception as e:
                print(f"DEBUG: Erro ao processar mídia: {e}")
                import traceback
                traceback.print_exc()
        
        # 5. Salvar mensagem recebida - VERIFICAR DUPLICATA
        # Verificar se já existe uma mensagem com o mesmo conteúdo nos últimos 30 segundos
        recent_time = timezone.now() - timedelta(seconds=30)
        existing_message = Message.objects.filter(
            conversation=conversation,
            content=content,
            created_at__gte=recent_time,
            is_from_customer=True
        ).first()
        
        if existing_message:
            content_preview = content[:30] if content else "sem conteúdo"
            print(f"  Mensagem duplicada detectada: {content_preview}... - Ignorando duplicata")
            return JsonResponse({'status': 'ignored_duplicate'}, status=200)
        
        # Adicionar informações de resposta se for uma mensagem respondida
        print(f"DEBUG: Verificando se é mensagem respondida:")
        print(f"DEBUG: quoted_message: {quoted_message}")
        print(f"DEBUG: reply_to_message_id: {reply_to_message_id}")
        print(f"DEBUG: reply_to_content: {reply_to_content}")
        
        if quoted_message and reply_to_content:
            additional_attrs['is_reply'] = True
            additional_attrs['reply_to_message_id'] = reply_to_message_id or quoted_id
            additional_attrs['reply_to_content'] = reply_to_content
            print(f"DEBUG: Mensagem respondida detectada - ID: {reply_to_message_id or quoted_id}, Conteúdo: {reply_to_content}")
        else:
            print(f"DEBUG: Não é mensagem respondida ou faltam informações")
            print(f"DEBUG: quoted_message: {quoted_message}")
            print(f"DEBUG: reply_to_message_id: {reply_to_message_id}")
            print(f"DEBUG: reply_to_content: {reply_to_content}")
        
        # Determinar o tipo de mensagem para salvar no banco
        db_message_type = message_type if message_type in ['audio', 'image', 'video', 'document', 'sticker', 'ptt', 'media'] else 'incoming'
        
        # Se for mensagem de mídia mas o message_type não for reconhecido, usar o media_type
        if db_message_type == 'incoming' and media_type in ['ptt', 'audio', 'image', 'video', 'document', 'sticker']:
            db_message_type = media_type
            print(f"DEBUG: Usando media_type como db_message_type: {media_type}")
        
        # Correção específica para áudio: se message_type é 'media' e media_type é 'ptt', usar 'ptt'
        if message_type == 'media' and media_type == 'ptt':
            db_message_type = 'ptt'
            print(f"DEBUG: Corrigindo db_message_type de 'media' para 'ptt'")
        
        # Correção para áudio detectado pelo mimetype
        if is_audio_message:
            db_message_type = 'audio'
            print(f"DEBUG: Corrigindo db_message_type para 'audio' baseado no mimetype")
        
        # Correção para imagem: se message_type é 'media' e media_type é 'image', usar 'image'
        if message_type == 'media' and media_type == 'image':
            db_message_type = 'image'
            print(f"DEBUG: Corrigindo db_message_type de 'media' para 'image'")
        
        # Correção para vídeo: se message_type é 'media' e media_type é 'video', usar 'video'
        if message_type == 'media' and media_type == 'video':
            db_message_type = 'video'
            print(f"DEBUG: Corrigindo db_message_type de 'media' para 'video'")
        
        # Correção para documento: se message_type é 'media' e media_type é 'document', usar 'document'
        if message_type == 'media' and media_type == 'document':
            db_message_type = 'document'
            print(f"DEBUG: Corrigindo db_message_type de 'media' para 'document'")
        
        print(f"DEBUG: db_message_type final: {db_message_type}")
        
        # Extrair dados de mídia dos additional_attrs
        file_url_value = additional_attrs.get('local_file_url') or additional_attrs.get('file_url') or getattr(locals(), 'file_url', None)
        file_name_value = additional_attrs.get('file_name') or getattr(locals(), 'filename', None)
        file_size_value = additional_attrs.get('file_size') or getattr(locals(), 'file_size', None)
        
        msg = Message.objects.create(
            conversation=conversation,
            message_type=db_message_type,
            content=content or '',
            is_from_customer=is_from_customer,  # Usar a variável controlada
            external_id=external_id,  # Salvar external_id no campo correto
            file_url=file_url_value,
            file_name=file_name_value,
            file_size=file_size_value,
            additional_attributes=additional_attrs,
            created_at=timezone.now()
        )
        content_preview = str(content)[:30] if content else "sem conteúdo"
        print(f"DEBUG: Nova mensagem salva: {msg.id} - Conversa: {conversation.id}, Contato: {contact.name} - {content_preview}...")
        print(f"DEBUG: Additional attributes salvos: {additional_attrs}")
        if file_url:
            print(f"DEBUG: Mensagem com mídia - file_url: {file_url}")
        
        # PROCESSAR PDFs AUTOMATICAMENTE
        pdf_ja_respondeu = False  # Inicializar variável
        print(f"DEBUG: Verificando processamento de PDF - db_message_type: {db_message_type}, file_url_value: {file_url_value}, file_name_value: {file_name_value}")
        print(f"DEBUG: Content original para verificação: {content}")
        if db_message_type == 'document' and file_url_value:
            # Verificar se é um PDF - usar msg_data que contém o content original
            is_pdf = False
            print(f"DEBUG: msg_data para verificação: {msg_data}")
            
            # Verificar no msg_data que contém o content original
            if isinstance(msg_data, dict) and 'content' in msg_data:
                msg_content = msg_data['content']
                print(f"DEBUG: msg_content para verificação: {msg_content}")
                
                if isinstance(msg_content, dict) and msg_content.get('mimetype') == 'application/pdf':
                    is_pdf = True
                    print(f"DEBUG: PDF detectado por mimetype: {msg_content.get('mimetype')}")
                elif file_name_value and file_name_value.lower().endswith('.pdf'):
                    is_pdf = True
                    print(f"DEBUG: PDF detectado por extensão: {file_name_value}")
            else:
                print(f"DEBUG: msg_data não contém content válido")
            
            if is_pdf:
                print(f"DEBUG: PDF detectado - iniciando processamento com pdfplumber")
                print(f"DEBUG: Content do PDF: {msg_content}")
                print(f"DEBUG: File URL: {file_url_value}")
                try:
                    # Importar dependências necessárias
                    from core.openai_service import openai_service
                    from core.pdf_processor import pdf_processor
                    import requests
                    import os
                    
                    print(f"DEBUG: PDF detectado: {file_name_value}")
                    print(f"DEBUG: Content completo: {content}")
                    print(f"DEBUG: File URL: {file_url_value}")
                    
                    # Baixar o PDF usando a API da Uazapi
                    print(f"DEBUG: Baixando PDF usando API da Uazapi...")
                    
                    # Usar a API da Uazapi para baixar o arquivo
                    uazapi_url = provedor.integracoes_externas.get('whatsapp_url')
                    uazapi_token = provedor.integracoes_externas.get('whatsapp_token')
                    download_url = f"{uazapi_url}/message/download"
                    download_payload = {
                        'id': message_id,
                        'return_base64': False,
                        'return_link': True,
                    }
                    
                    # Headers com autenticação
                    headers = {
                        'token': uazapi_token,
                        'Content-Type': 'application/json'
                    }
                    
                    print(f"DEBUG: Fazendo download via API: {download_url}")
                    print(f"DEBUG: Payload: {download_payload}")
                    
                    response = requests.post(download_url, json=download_payload, headers=headers, timeout=30)
                    if response.status_code == 200:
                        # A API retorna um JSON com fileURL
                        download_result = response.json()
                        print(f"DEBUG: Resposta da API: {download_result}")
                        
                        if 'fileURL' in download_result:
                            # Baixar o arquivo da URL retornada
                            file_url = download_result['fileURL']
                            print(f"DEBUG: Baixando arquivo de: {file_url}")
                            
                            file_response = requests.get(file_url, timeout=30)
                            if file_response.status_code == 200:
                                # Salvar temporariamente
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                                    temp_file.write(file_response.content)
                                    temp_pdf_path = temp_file.name
                                
                                print(f"DEBUG: PDF salvo temporariamente em: {temp_pdf_path}")
                                
                                # Verificar se o arquivo é realmente um PDF
                                with open(temp_pdf_path, 'rb') as f:
                                    file_content = f.read()
                                    print(f"DEBUG: Tamanho do arquivo: {len(file_content)} bytes")
                                    
                                    if file_content.startswith(b'%PDF-'):
                                        print(f"DEBUG: Arquivo é um PDF válido, iniciando processamento...")
                                        # Processar PDF com IA
                                        print(f"DEBUG: Iniciando processamento do PDF com IA...")
                                        pdf_result = openai_service.process_pdf_with_ai(
                                            pdf_path=temp_pdf_path,
                                            provedor=provedor,
                                            contexto={
                                                'conversation_id': conversation.id,
                                                'contact_name': contact.name,
                                                'file_name': file_name_value
                                            }
                                        )
                                        
                                        print(f"DEBUG: Resultado do processamento PDF: {pdf_result}")
                                        
                                        # Limpar arquivo temporário
                                        try:
                                            os.unlink(temp_pdf_path)
                                        except:
                                            pass
                                        
                                        # Se o PDF foi processado com sucesso, atualizar o conteúdo para a IA
                                        if pdf_result['success']:
                                            print(f"DEBUG: PDF processado com sucesso: {pdf_result['resposta'][:100]}...")
                                            
                                            # Atualizar o conteúdo para que a IA processe o conteúdo do PDF
                                            content = pdf_result['resposta']
                                            
                                            # Adicionar informações do PDF ao contexto para a IA
                                            if 'additional_attrs' not in locals():
                                                additional_attrs = {}
                                            additional_attrs['pdf_processed'] = True
                                            additional_attrs['pdf_info'] = pdf_result.get('pdf_info', {})
                                            additional_attrs['file_name'] = file_name_value
                                            
                                            # Atualizar mensagem existente com as informações do PDF
                                            msg.content = content
                                            msg.additional_attributes = additional_attrs
                                            msg.save()
                                            
                                            print(f"DEBUG: PDF processado com sucesso - conteúdo atualizado: {content[:100]}...")
                                            
                                            # Definir a resposta da IA como sendo a resposta do processamento do PDF
                                            resposta_ia = pdf_result['resposta']
                                            ia_result = {
                                                'success': True,
                                                'resposta': pdf_result['resposta'],
                                                'model': 'gpt-4.1',
                                                'provedor': provedor.nome,
                                                'satisfacao_detectada': False
                                            }
                                            print(f"DEBUG: Usando resposta do processamento do PDF como resposta final")
                                            
                                            # Marcar que o PDF já foi processado e respondeu para evitar chamada duplicada da IA
                                            pdf_ja_respondeu = True
                                        else:
                                            print(f"DEBUG: Erro ao processar PDF: {pdf_result.get('erro', 'Erro desconhecido')}")
                                    else:
                                        print(f"DEBUG: Arquivo não é um PDF válido (não começa com %PDF-)")
                                        pdf_result = {
                                            'success': False,
                                            'erro': 'Arquivo não é um PDF válido',
                                            'pdf_info': {'is_payment_receipt': False, 'message': 'Arquivo não é um PDF válido'}
                                        }
                                        
                                        # Limpar arquivo temporário
                                        try:
                                            os.unlink(temp_pdf_path)
                                        except:
                                            pass
                            else:
                                print(f"DEBUG: Erro ao baixar arquivo: {file_response.status_code}")
                                pdf_result = {
                                    'success': False,
                                    'erro': 'Erro ao baixar arquivo',
                                    'pdf_info': {'is_payment_receipt': False, 'message': 'Erro ao baixar o arquivo'}
                                }
                        else:
                            print(f"DEBUG: fileURL não encontrado na resposta")
                            pdf_result = {
                                'success': False,
                                'erro': 'fileURL não encontrado',
                                'pdf_info': {'is_payment_receipt': False, 'message': 'URL do arquivo não encontrada'}
                            }
                    else:
                        print(f"DEBUG: Erro na API: {response.status_code} - {response.text}")
                        pdf_result = {
                            'success': False,
                            'erro': 'Erro na API da Uazapi',
                            'pdf_info': {'is_payment_receipt': False, 'message': 'Erro ao acessar a API'}
                        }
                        
                except Exception as pdf_error:
                    print(f"DEBUG: Erro ao processar PDF: {pdf_error}")
            else:
                print(f"DEBUG: Arquivo não é PDF - mimetype: {content.get('mimetype') if isinstance(content, dict) else 'N/A'}, extensão: {file_name_value}")
        
        # PROCESSAR IMAGENS AUTOMATICAMENTE
        print(f"DEBUG: Verificando processamento de imagem - db_message_type: {db_message_type}, file_url_value: {file_url_value}, file_name_value: {file_name_value}")
        if db_message_type in ['image', 'media'] and file_url_value:
            # Verificar se é uma imagem usando msg_data original
            is_image = False
            if isinstance(msg_data, dict) and 'content' in msg_data:
                msg_content = msg_data['content']
                if isinstance(msg_content, dict) and msg_content.get('mimetype', '').startswith('image/'):
                    is_image = True
                    print(f"DEBUG: Imagem detectada por mimetype: {msg_content.get('mimetype')}")
            elif file_name_value and file_name_value.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                is_image = True
                print(f"DEBUG: Imagem detectada por extensão: {file_name_value}")
            
            if is_image:
                print(f"DEBUG: Imagem confirmada - iniciando processamento com IA")
                try:
                    # Baixar a imagem usando a API da Uazapi
                    print(f"DEBUG: Baixando imagem usando API da Uazapi...")
                    
                    uazapi_url = provedor.integracoes_externas.get('whatsapp_url')
                    download_url = f"{uazapi_url}/message/download"
                    uazapi_token = provedor.integracoes_externas.get('whatsapp_token')
                    download_payload = {
                        'id': message_id,
                        'return_base64': False,
                        'return_link': True,
                    }
                    
                    headers = {
                        'token': uazapi_token,
                        'Content-Type': 'application/json'
                    }
                    
                    print(f"DEBUG: Fazendo download via API: {download_url}")
                    print(f"DEBUG: Payload: {download_payload}")
                    
                    response = requests.post(download_url, json=download_payload, headers=headers, timeout=30)
                    if response.status_code == 200:
                        download_result = response.json()
                        print(f"DEBUG: Resposta da API: {download_result}")
                        
                        if 'fileURL' in download_result:
                            file_url = download_result['fileURL']
                            print(f"DEBUG: Baixando imagem de: {file_url}")
                            
                            file_response = requests.get(file_url, timeout=30)
                            if file_response.status_code == 200:
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                                    temp_file.write(file_response.content)
                                    temp_image_path = temp_file.name
                                    
                                print(f"DEBUG: Imagem salva temporariamente em: {temp_image_path}")
                                
                                # Verificar se o arquivo é realmente uma imagem
                                with open(temp_image_path, 'rb') as f:
                                    file_content = f.read()
                                    print(f"DEBUG: Tamanho da imagem: {len(file_content)} bytes")
                                    
                                    # Verificar se é uma imagem válida (JPEG, PNG, etc.)
                                    if (file_content.startswith(b'\xff\xd8\xff') or  # JPEG
                                        file_content.startswith(b'\x89PNG') or      # PNG
                                        file_content.startswith(b'GIF8') or         # GIF
                                        file_content.startswith(b'RIFF')):          # WEBP
                                        
                                        print(f"DEBUG: Imagem válida detectada, iniciando análise com IA...")
                                        
                                        # Processar imagem com IA
                                        from core.openai_service import openai_service
                                        ai_response = openai_service.analyze_image_with_ai(
                                            image_path=temp_image_path,
                                            provedor=provedor,
                                            contexto={
                                                'conversation_id': conversation.id,
                                                'contact_name': contact.name,
                                                'file_name': file_name_value,
                                                'image_url': file_url
                                            }
                                        )
                                        
                                        if ai_response['success']:
                                            print(f"DEBUG: Análise da imagem concluída: {ai_response['resposta'][:100]}...")
                                            
                                            # Verificar se deve transferir para suporte (LED vermelho detectado)
                                            if ai_response.get('transferir_suporte', False):
                                                print(f"DEBUG: LED vermelho detectado - transferindo para suporte")
                                                # Aqui você pode adicionar lógica para transferir para suporte
                                                # Por exemplo, marcar conversa como "precisa de suporte técnico"
                                            
                                            # Enviar resposta da IA sobre a imagem
                                            from integrations.utils import send_whatsapp_message
                                            send_result = send_whatsapp_message(
                                                phone=contact.phone,
                                                message=ai_response['resposta'],
                                                provedor=provedor
                                            )
                                            
                                            if send_result:
                                                print(f"DEBUG: Resposta automática sobre imagem enviada para {contact.phone}")
                                                Message.objects.create(
                                                    conversation=conversation,
                                                    message_type='outgoing',
                                                    content=ai_response['resposta'],
                                                    is_from_customer=False,
                                                    additional_attributes={
                                                        'auto_response': True,
                                                        'image_analyzed': True,
                                                        'led_vermelho_detectado': ai_response.get('led_vermelho_detectado', False),
                                                        'transferir_suporte': ai_response.get('transferir_suporte', False),
                                                        'file_name': file_name_value
                                                    },
                                                    created_at=timezone.now()
                                                )
                                                
                                                # Imagem processada com sucesso - retornar para evitar processamento adicional pela IA
                                                print(f"DEBUG: Imagem processada com sucesso - finalizando processamento")
                                                return JsonResponse({'status': 'image_processed_successfully', 'ai_response_sent': True})
                                            else:
                                                print(f"DEBUG: Erro ao enviar resposta automática sobre imagem")
                                                # Mesmo com erro no envio, salvar a resposta da IA no banco
                                                Message.objects.create(
                                                    conversation=conversation,
                                                    message_type='outgoing',
                                                    content=ai_response['resposta'],
                                                    is_from_customer=False,
                                                    additional_attributes={
                                                        'auto_response': True,
                                                        'image_analyzed': True,
                                                        'led_vermelho_detectado': ai_response.get('led_vermelho_detectado', False),
                                                        'transferir_suporte': ai_response.get('transferir_suporte', False),
                                                        'file_name': file_name_value,
                                                        'send_error': True
                                                    },
                                                    created_at=timezone.now()
                                                )
                                                
                                                # Imagem processada com sucesso - retornar para evitar processamento adicional pela IA
                                                print(f"DEBUG: Imagem processada com sucesso (com erro no envio) - finalizando processamento")
                                                return JsonResponse({'status': 'image_processed_successfully', 'ai_response_saved': True, 'send_error': True})
                                        else:
                                            print(f"DEBUG: Erro na análise da imagem: {ai_response.get('erro', 'Erro desconhecido')}")
                                    
                                    # Limpar arquivo temporário
                                    try:
                                        os.unlink(temp_image_path)
                                    except:
                                        pass
                            else:
                                print(f"DEBUG: Erro ao baixar imagem: {file_response.status_code}")
                        else:
                            print(f"DEBUG: fileURL não encontrado na resposta")
                    else:
                        print(f"DEBUG: Erro na API: {response.status_code} - {response.text}")
                        
                except Exception as image_error:
                    print(f"DEBUG: Erro ao processar imagem: {image_error}")
                    traceback.print_exc()
            else:
                print(f"DEBUG: Arquivo não é uma imagem - mimetype: {content.get('mimetype') if isinstance(content, dict) else 'N/A'}, extensão: {file_name_value}")

        # SALVAR MENSAGEM NO REDIS (UAZAPI WEBHOOK)
        try:
            from core.redis_memory_service import redis_memory_service
            sender_type = 'customer' if is_from_customer else 'agent'
            redis_memory_service.add_message_to_conversation_sync(
                provedor_id=provedor.id,
                conversation_id=conversation.id,
                sender=sender_type,
                content=content or '',
                message_type=db_message_type
            )
        except Exception as e:
            logger.warning(f"Erro ao salvar mensagem no Redis: {e}")
        
        # Emitir evento WebSocket para a conversa específica
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        from conversations.serializers import MessageSerializer
        message_data = MessageSerializer(msg).data
        
        async_to_sync(channel_layer.group_send)(
            f'conversation_{conversation.id}',
            {
                'type': 'chat_message',
                'message': message_data,
                'sender': None,
                'timestamp': msg.created_at.isoformat(),
            }
        )
        
        # Emitir evento WebSocket para o dashboard
        from conversations.serializers import ConversationSerializer
        async_to_sync(channel_layer.group_send)(
            'conversas_dashboard',
            {
                'type': 'dashboard_event',
                'data': {
                    'action': 'update_conversation',
                    'conversation': ConversationSerializer(conversation).data
                }
            }
        )
        
        # 1. Verificar se é resposta CSAT (emoji de feedback)
        from conversations.csat_service import CSATService
        
        csat_feedback = None
        if content and str(content).strip():
            # Tentar processar como feedback CSAT primeiro
            csat_feedback = CSATService.process_csat_response(
                message_content=str(content),
                contact=contact,
                conversation=conversation
            )
            
            if csat_feedback:
                print(f"📊 CSAT: Feedback processado - {csat_feedback.emoji_rating} ({csat_feedback.rating_value})")
                # Se foi processado como CSAT, não enviar para IA
                return JsonResponse({'success': True, 'csat_processed': True, 'rating': csat_feedback.emoji_rating})
        
        # 2.a Se for áudio, tentar baixar/transcrever via Uazapi e anexar ao conteúdo para IA
        try:
            if db_message_type in ['audio', 'ptt'] and 'id' in msg_data:
                audio_msg_id = (msg_data.get('id') or msg_data.get('messageId') or msg_data.get('messageid') or msg_data.get('key', {}).get('id'))
                if audio_msg_id:
                    from core.uazapi_client import UazapiClient
                    client = UazapiClient(uazapi_url, uazapi_token)
                    
                    # CONFIGURAÇÕES DINÂMICAS DE TRANSCRIÇÃO POR PROVEDOR
                    transcription_config = provedor.integracoes_externas.get('transcription_config', {})
                    language = transcription_config.get('language', 'pt-BR')
                    quality = transcription_config.get('quality', 'high')
                    delay_between = transcription_config.get('delay_between', 1)
                    enable_double = transcription_config.get('enable_double_transcription', True)
                    
                    print(f"🎵 CONFIGURAÇÕES DE TRANSCRIÇÃO - Provedor: {provedor.nome}")
                    print(f"🎵 Idioma: {language}, Qualidade: {quality}, Delay: {delay_between}s, Dupla: {enable_double}")
                    
                    # Usar chave OpenAI do sistema/provedor se disponível
                    # Priorizar chave do Superadmin (SystemConfig); fallback para provedor
                    from core.models import SystemConfig
                    cfg = SystemConfig.objects.first()
                    openai_key = None
                    if cfg and cfg.openai_api_key:
                        openai_key = cfg.openai_api_key
                    elif hasattr(provedor, 'openai_api_key') and provedor.openai_api_key:
                        openai_key = provedor.openai_api_key
                    
                    # PRIMEIRA TRANSCRIÇÃO
                    print(f"🎵 PRIMEIRA TRANSCRIÇÃO: Iniciando para áudio ID {audio_msg_id}")
                    dl1 = client.download_message(
                        message_id=audio_msg_id,
                        generate_mp3=True,
                        return_base64=False,
                        return_link=True,
                        transcribe=True,
                        openai_apikey=openai_key
                    )
                    transcription1 = dl1.get('transcription') if isinstance(dl1, dict) else None
                    
                    # Delay dinâmico entre transcrições
                    if enable_double:
                        print(f"⏳ Aguardando {delay_between} segundo(s) entre transcrições...")
                        import time
                        time.sleep(delay_between)
                        
                        # SEGUNDA TRANSCRIÇÃO (para garantir precisão)
                        print(f"🎵 SEGUNDA TRANSCRIÇÃO: Iniciando para áudio ID {audio_msg_id}")
                        dl2 = client.download_message(
                            message_id=audio_msg_id,
                            generate_mp3=True,
                            return_base64=False,
                            return_link=True,
                            transcribe=True,
                            openai_apikey=openai_key
                        )
                        transcription2 = dl2.get('transcription') if isinstance(dl2, dict) else None
                        
                        # COMPARAR TRANSCRIÇÕES E ESCOLHER A MELHOR
                        final_transcription = None
                        if transcription1 and transcription2:
                            print(f"🎵 TRANSCRIÇÃO 1: {transcription1}")
                            print(f"🎵 TRANSCRIÇÃO 2: {transcription2}")
                            
                            # Se as transcrições são idênticas, usar qualquer uma
                            if transcription1.strip().lower() == transcription2.strip().lower():
                                final_transcription = transcription1
                                print(f"🎵 TRANSCRIÇÕES IDÊNTICAS: Usando transcrição 1")
                            else:
                                # Se diferentes, usar a mais longa (geralmente mais precisa)
                                if len(transcription1) > len(transcription2):
                                    final_transcription = transcription1
                                    print(f"🎵 TRANSCRIÇÕES DIFERENTES: Usando transcrição 1 (mais longa)")
                                else:
                                    final_transcription = transcription2
                                    print(f"🎵 TRANSCRIÇÕES DIFERENTES: Usando transcrição 2 (mais longa)")
                        elif transcription1:
                            final_transcription = transcription1
                            print(f"🎵 APENAS TRANSCRIÇÃO 1 DISPONÍVEL: {transcription1}")
                        elif transcription2:
                            final_transcription = transcription2
                            print(f"🎵 APENAS TRANSCRIÇÃO 2 DISPONÍVEL: {transcription2}")
                        else:
                            print(f"🎵 NENHUMA TRANSCRIÇÃO OBTIDA para áudio ID {audio_msg_id}")
                    else:
                        # TRANSCRIÇÃO ÚNICA (quando dupla está desabilitada)
                        final_transcription = transcription1
                        print(f"🎵 TRANSCRIÇÃO ÚNICA: {transcription1}")
                    
                    if final_transcription:
                        additional_attrs['transcription'] = final_transcription
                        additional_attrs['transcription1'] = transcription1
                        additional_attrs['transcription2'] = transcription2 if enable_double else None
                        additional_attrs['transcription_config'] = {
                            'language': language,
                            'quality': quality,
                            'delay_between': delay_between,
                            'enable_double': enable_double,
                            'provedor': provedor.nome
                        }
                        # Usar a transcrição final como conteúdo para IA
                        content = final_transcription
                        print(f"🎵 TRANSCRIÇÃO FINAL PARA IA: {final_transcription[:120]}...")
                    else:
                        print(f"🎵 NENHUMA TRANSCRIÇÃO OBTIDA para áudio ID {audio_msg_id}")
        except Exception as e:
            print(f"[WARN] Falha ao transcrever áudio via Uazapi: {e}")
            import traceback
            traceback.print_exc()

        # 2. Acionar IA para resposta automática (apenas se não foi CSAT e não estiver atribuída)
        
        # Verificar se o PDF já foi processado e respondeu para evitar chamada duplicada da IA
        if pdf_ja_respondeu:
            print(f"DEBUG: PDF já foi processado e respondeu, pulando chamada da IA principal")
            # A resposta já foi definida no processamento do PDF, não fazer nada aqui
        elif content and str(content).strip():  # Verificar se há conteúdo válido antes de chamar a IA
            # Importar openai_service
            from core.openai_service import openai_service
            
            # Verificar se conversa está atribuída ou em espera
            if conversation.assignee is None and conversation.status != 'pending':
                print(f"🤖 IA: Acionando IA para mensagem: {content[:50]}...")
                try:
                    ia_result = openai_service.generate_response_sync(
                        mensagem=str(content),  # Garantir que é string
                        provedor=provedor,
                        contexto={'conversation': conversation}
                    )
                except Exception as e:
                    print(f"🤖 IA: Erro ao gerar resposta: {str(e)}")
                    ia_result = {'success': False, 'erro': str(e)}
            else:
                print(f"🤖 IA: Não acionada - Conversa atribuída ao agente {conversation.assignee.username if conversation.assignee else 'N/A'} ou em espera (status: {conversation.status})")
                ia_result = {'success': False, 'motivo': 'Conversa atribuída ou em espera'}
                
            try:
                print(f"🤖 IA: Resultado: {ia_result}")
            except Exception as e:
                print(f"❌ ERRO na IA: {str(e)}")
                import traceback
                traceback.print_exc()
                ia_result = {'success': False, 'erro': f'Erro na IA: {str(e)}'}
        else:
            print("⚠️ IA: Mensagem sem conteúdo válido, pulando geração de resposta")
            ia_result = {'success': False, 'erro': 'Mensagem sem conteúdo válido'}
        
        # Definir resposta_ia baseada no processamento do PDF ou da IA
        if pdf_ja_respondeu:
            # Se o PDF foi processado, usar a resposta do PDF que já foi definida
            if 'resposta_ia' in locals() and resposta_ia:
                # resposta_ia já foi definida no processamento do PDF
                pass
            elif 'ia_result' in locals() and ia_result.get('success'):
                resposta_ia = ia_result.get('resposta')
            else:
                # Usar o conteúdo que foi processado pelo PDF
                resposta_ia = content if content else None
        else:
            # Se não foi PDF, usar a resposta da IA
            resposta_ia = ia_result.get('resposta') if ia_result.get('success') else None
        # 3. Enviar resposta para Uazapi (WhatsApp)
        import requests
        send_result = None
        success = False
        if resposta_ia and uazapi_token and uazapi_url:
            # Usar APENAS chatid para envio da resposta da IA
            destination_number = chatid_full
            if destination_number:
                try:
                    # Limpar o número (remover @s.whatsapp.net se presente)
                    clean_number = destination_number.replace('@s.whatsapp.net', '').replace('@c.us', '')
                    
                    payload = {
                        'number': clean_number,
                        'text': resposta_ia
                    }
                    print(f"DEBUG: Enviando resposta IA para: {clean_number}")
                    send_resp = requests.post(
                        f"{uazapi_url.rstrip('/')}/send/text",
                        headers={'token': uazapi_token, 'Content-Type': 'application/json'},
                        json=payload,
                        timeout=10
                    )
                    if send_resp.status_code == 200:
                        send_result = send_resp.json() if send_resp.content else send_resp.status_code
                        success = True
                        print(f"DEBUG: Mensagem enviada com sucesso para {clean_number}")
                    else:
                        print(f"DEBUG: Erro ao enviar para {clean_number} - Status: {send_resp.status_code}")
                except Exception as e:
                    print(f'[ERRO] Erro ao enviar para {destination_number}: {e}')
            else:
                print(f"DEBUG: Nenhum chatid encontrado para envio da resposta da IA")
            # Salvar mensagem enviada pela IA na conversa - VERIFICAR DUPLICATA
            if success and resposta_ia:
                # Verificar se já existe uma mensagem da IA com o mesmo conteúdo nos últimos 30 segundos
                recent_time = timezone.now() - timedelta(seconds=30)
                existing_ia_message = Message.objects.filter(
                    conversation=conversation,
                    content=resposta_ia,
                    created_at__gte=recent_time,
                    is_from_customer=False
                ).first()
                
                if existing_ia_message:
                    resposta_preview = str(resposta_ia)[:30] if resposta_ia else "sem resposta"
                    print(f"  Mensagem da IA duplicada ignorada: {resposta_preview}...")
                else:
                    msg_ia = Message.objects.create(
                        conversation=conversation,
                        message_type='outgoing',
                        content=resposta_ia,
                        is_from_customer=False,
                        created_at=timezone.now()
                    )
                    resposta_preview = str(resposta_ia)[:30] if resposta_ia else "sem resposta"
                    print(f"DEBUG: Mensagem da IA salva: {msg_ia.id} - Conversa: {conversation.id}, Contato: {contact.name} - {resposta_preview}...")
                    
                    # SALVAR MENSAGEM DA IA NO REDIS (UAZAPI WEBHOOK)
                    try:
                        from core.redis_memory_service import redis_memory_service
                        redis_memory_service.add_message_to_conversation_sync(
                            provedor_id=provedor.id,
                            conversation_id=conversation.id,
                            sender='ai',
                            content=resposta_ia,
                            message_type='text'
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao salvar mensagem da IA no Redis: {e}")
                    
                    # Emitir evento WebSocket para mensagem da IA
                    async_to_sync(channel_layer.group_send)(
                        f'conversation_{conversation.id}',
                        {
                            'type': 'chat_message',
                            'message': MessageSerializer(msg_ia).data,
                            'sender': None,
                            'timestamp': msg_ia.created_at.isoformat(),
                        }
                    )
        # Retornar 'ok' se a mensagem foi processada, independente do sucesso da resposta da IA
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        print(f'[ERRO] Erro no webhook: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)

