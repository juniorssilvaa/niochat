from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.files.storage import default_storage
import uuid
import os

from .models import (
    InternalChatRoom, 
    InternalChatParticipant, 
    InternalChatMessage, 
    InternalChatMessageRead, 
    InternalChatReaction
)
from .serializers_internal_chat import (
    InternalChatRoomSerializer,
    InternalChatMessageSerializer,
    InternalChatParticipantSerializer,
    InternalChatReactionSerializer,
    InternalChatMessageCreateSerializer
)

class InternalChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet para salas de chat interno
    """
    serializer_class = InternalChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Buscar provedor do usuário
        provedor = getattr(user, 'provedor', None) or user.provedores_admin.first()
        
        if not provedor:
            return InternalChatRoom.objects.none()
        
        # Garantir que existe uma sala geral do provedor
        self._ensure_provider_room_exists(user, provedor)
            
        # Retornar apenas salas do provedor onde o usuário participa
        return InternalChatRoom.objects.filter(
            provedor=provedor,
            participants__user=user,
            is_active=True
        ).prefetch_related(
            'participants__user',
            Prefetch('messages', queryset=InternalChatMessage.objects.select_related('sender').order_by('-created_at')[:50])
        ).distinct()
    
    def _ensure_provider_room_exists(self, user, provedor):
        """
        Garantir que existe uma sala geral do provedor
        """
        room, created = InternalChatRoom.objects.get_or_create(
            provedor=provedor,
            room_type='general',
            defaults={
                'name': f'Chat Geral - {provedor.name}',
                'description': 'Chat geral do provedor',
                'created_by': user
            }
        )
        
        # Se a sala foi criada, adicionar todos os usuários do provedor
        if created:
            users = provedor.user_set.all()
            for u in users:
                InternalChatParticipant.objects.create(
                    room=room,
                    user=u
                )
        
        # Garantir que o usuário atual seja participante
        InternalChatParticipant.objects.get_or_create(
            room=room,
            user=user
        )
    
    def perform_create(self, serializer):
        user = self.request.user
        provedor = getattr(user, 'provedor', None) or user.provedores_admin.first()
        
        room = serializer.save(
            provedor=provedor,
            created_by=user
        )
        
        # Adicionar o criador como participante admin
        InternalChatParticipant.objects.create(
            room=room,
            user=user,
            is_admin=True
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Participar de uma sala
        """
        room = self.get_object()
        user = request.user
        
        participant, created = InternalChatParticipant.objects.get_or_create(
            room=room,
            user=user,
            defaults={'is_active': True}
        )
        
        if not created:
            participant.is_active = True
            participant.save()
        
        # Notificar outros participantes
        self._notify_room_event(room, 'user_joined', {
            'user_id': user.id,
            'username': user.username,
            'user_name': f"{user.first_name} {user.last_name}".strip() or user.username
        })
        
        return Response({'message': 'Participou da sala com sucesso'})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Sair de uma sala
        """
        room = self.get_object()
        user = request.user
        
        try:
            participant = InternalChatParticipant.objects.get(room=room, user=user)
            participant.is_active = False
            participant.save()
            
            # Notificar outros participantes
            self._notify_room_event(room, 'user_left', {
                'user_id': user.id,
                'username': user.username,
                'user_name': f"{user.first_name} {user.last_name}".strip() or user.username
            })
            
            return Response({'message': 'Saiu da sala com sucesso'})
        except InternalChatParticipant.DoesNotExist:
            return Response({'error': 'Não está participando desta sala'}, status=400)
    
    def _notify_room_event(self, room, event_type, data):
        """
        Notificar evento da sala via WebSocket
        """
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"internal_chat_{room.id}",
            {
                'type': 'room_event',
                'event_type': event_type,
                'data': data
            }
        )

class InternalChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para mensagens do chat interno
    """
    serializer_class = InternalChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        user = self.request.user
        room_id = self.request.query_params.get('room_id')
        
        if not room_id:
            return InternalChatMessage.objects.none()
        
        # Verificar se o usuário participa da sala
        try:
            room = InternalChatRoom.objects.get(id=room_id)
            if not room.participants.filter(user=user, is_active=True).exists():
                return InternalChatMessage.objects.none()
        except InternalChatRoom.DoesNotExist:
            return InternalChatMessage.objects.none()
        
        return InternalChatMessage.objects.filter(
            room_id=room_id,
            is_deleted=False
        ).select_related('sender', 'reply_to__sender').prefetch_related('reactions__user').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InternalChatMessageCreateSerializer
        return InternalChatMessageSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        room_id = self.request.data.get('room_id')
        
        # Se não há room_id, obter ou criar sala geral do provedor
        if not room_id:
            room = self._get_or_create_provider_room(user)
        else:
            room = get_object_or_404(InternalChatRoom, id=room_id)
            if not room.participants.filter(user=user, is_active=True).exists():
                raise permissions.PermissionDenied("Você não tem permissão para enviar mensagens nesta sala")
        
        # Processar upload de arquivo se houver
        file_data = self._handle_file_upload(self.request)
        
        message = serializer.save(
            sender=user,
            room=room,
            **file_data
        )
        
        # Marcar como lida pelo remetente
        InternalChatMessageRead.objects.create(
            message=message,
            user=user
        )
        
        # Notificar via WebSocket
        self._notify_new_message(message)
        
        return message
    
    def _get_or_create_provider_room(self, user):
        """
        Obter ou criar sala geral do provedor
        """
        from core.models import Provedor
        
        # Buscar ou criar sala geral do provedor
        room, created = InternalChatRoom.objects.get_or_create(
            provedor=user.provedor,
            room_type='general',
            defaults={
                'name': f'Chat Geral - {user.provedor.name}',
                'description': 'Chat geral do provedor',
                'created_by': user
            }
        )
        
        # Se a sala foi criada, adicionar todos os usuários do provedor
        if created:
            users = user.provedor.user_set.all()
            for u in users:
                InternalChatParticipant.objects.create(
                    room=room,
                    user=u
                )
        
        # Garantir que o usuário atual seja participante
        InternalChatParticipant.objects.get_or_create(
            room=room,
            user=user
        )
        
        return room
    
    def _handle_file_upload(self, request):
        """
        Processar upload de arquivo
        """
        file_data = {}
        uploaded_file = request.FILES.get('file')
        
        if uploaded_file:
            # Gerar nome único
            file_extension = os.path.splitext(uploaded_file.name)[1]
            unique_filename = f"internal_chat/{uuid.uuid4()}{file_extension}"
            
            # Salvar arquivo
            file_path = default_storage.save(unique_filename, uploaded_file)
            file_url = default_storage.url(file_path)
            
            # Determinar tipo de mensagem baseado no arquivo
            if uploaded_file.content_type.startswith('image/'):
                message_type = 'image'
            elif uploaded_file.content_type.startswith('video/'):
                message_type = 'video'
            elif uploaded_file.content_type.startswith('audio/'):
                message_type = 'audio'
            else:
                message_type = 'file'
            
            file_data = {
                'file_url': file_url,
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'message_type': message_type
            }
        
        return file_data
    
    def _notify_new_message(self, message):
        """
        Notificar nova mensagem via WebSocket
        """
        channel_layer = get_channel_layer()
        
        # Serializar mensagem para envio
        from .serializers_internal_chat import InternalChatMessageSerializer
        message_data = InternalChatMessageSerializer(message).data
        
        # Notificar sala específica
        async_to_sync(channel_layer.group_send)(
            f"internal_chat_{message.room.id}",
            {
                'type': 'new_message',
                'message': message_data
            }
        )
        
        # Notificar todos os participantes da sala sobre contador atualizado
        participants = message.room.participants.filter(is_active=True)
        for participant in participants:
            if participant.user != message.sender:  # Não notificar o remetente
                # Calcular contador total de mensagens não lidas para este usuário em todas as salas
                provedor = getattr(participant.user, 'provedor', None) or participant.user.provedores_admin.first()
                if provedor:
                    user_rooms = InternalChatRoom.objects.filter(
                        provedor=provedor,
                        participants__user=participant.user,
                        participants__is_active=True,
                        is_active=True
                    )
                    
                    total_unread = 0
                    unread_by_sender = {}
                    
                    for room in user_rooms:
                        unread_count = room.messages.exclude(
                            read_receipts__user=participant.user
                        ).exclude(
                            sender=participant.user
                        ).count()
                        total_unread += unread_count
                        
                        # Contar mensagens não lidas por remetente
                        unread_messages = room.messages.exclude(
                            read_receipts__user=participant.user
                        ).exclude(
                            sender=participant.user
                        ).values('sender').annotate(
                            count=Count('id')
                        )
                        
                        for item in unread_messages:
                            sender_id = item['sender']
                            count = item['count']
                            if sender_id in unread_by_sender:
                                unread_by_sender[sender_id] += count
                            else:
                                unread_by_sender[sender_id] = count
                    
                    async_to_sync(channel_layer.group_send)(
                        f"internal_chat_notifications_{participant.user.id}",
                        {
                            'type': 'unread_count_update',
                            'total_unread': total_unread,
                            'unread_by_user': unread_by_sender
                        }
                    )
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Marcar mensagem como lida
        """
        message = self.get_object()
        user = request.user
        
        read_receipt, created = InternalChatMessageRead.objects.get_or_create(
            message=message,
            user=user
        )
        
        if created:
            # Notificar que a mensagem foi lida
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"internal_chat_{message.room.id}",
                {
                    'type': 'message_read',
                    'message_id': message.id,
                    'user_id': user.id
                }
            )
        
        return Response({'message': 'Mensagem marcada como lida'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Marcar todas as mensagens de uma sala como lidas
        """
        user = request.user
        
        # Tentar obter room_id de diferentes formas
        room_id = None
        if hasattr(request, 'data'):
            room_id = request.data.get('room_id')
        elif request.POST:
            room_id = request.POST.get('room_id')
        elif request.body:
            import json
            try:
                data = json.loads(request.body)
                room_id = data.get('room_id')
            except:
                pass
        
        if not room_id:
            return Response({'error': 'room_id é obrigatório'}, status=400)
        
        try:
            # Verificar se o usuário participa da sala
            room = InternalChatRoom.objects.get(
                id=room_id,
                participants__user=user,
                participants__is_active=True,
                is_active=True
            )
            
            # Buscar todas as mensagens não lidas da sala
            unread_messages = room.messages.exclude(
                read_receipts__user=user
            ).exclude(
                sender=user
            )
            
            # Marcar todas como lidas
            read_receipts = []
            for message in unread_messages:
                read_receipt, created = InternalChatMessageRead.objects.get_or_create(
                    message=message,
                    user=user
                )
                if created:
                    read_receipts.append(read_receipt)
            
            # Notificar atualização do contador
            self._notify_unread_count_update(user)
            
            return Response({
                'message': f'{len(read_receipts)} mensagens marcadas como lidas',
                'marked_count': len(read_receipts)
            })
            
        except InternalChatRoom.DoesNotExist:
            return Response({'error': 'Sala não encontrada ou usuário não participa'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def _notify_unread_count_update(self, user):
        """
        Notificar atualização do contador de mensagens não lidas
        """
        try:
            # Buscar provedor do usuário
            provedor = getattr(user, 'provedor', None) or user.provedores_admin.first()
            
            if not provedor:
                return
            
            # Buscar salas onde o usuário participa
            user_rooms = InternalChatRoom.objects.filter(
                provedor=provedor,
                participants__user=user,
                participants__is_active=True,
                is_active=True
            )
            
            # Contar mensagens não lidas
            total_unread = 0
            unread_by_sender = {}
            
            for room in user_rooms:
                unread_count = room.messages.exclude(
                    read_receipts__user=user
                ).exclude(
                    sender=user
                ).count()
                total_unread += unread_count
                
                # Contar mensagens não lidas por remetente
                unread_messages = room.messages.exclude(
                    read_receipts__user=user
                ).exclude(
                    sender=user
                ).values('sender').annotate(
                    count=Count('id')
                )
                
                for item in unread_messages:
                    sender_id = item['sender']
                    count = item['count']
                    if sender_id in unread_by_sender:
                        unread_by_sender[sender_id] += count
                    else:
                        unread_by_sender[sender_id] = count
            
            # Notificar via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"internal_chat_notifications_{user.id}",
                {
                    'type': 'unread_count_update',
                    'total_unread': total_unread,
                    'unread_by_user': unread_by_sender
                }
            )
            
        except Exception as e:
            print(f"Erro ao notificar atualização do contador: {e}")
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """
        Reagir a uma mensagem
        """
        message = self.get_object()
        user = request.user
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response({'error': 'Emoji é obrigatório'}, status=400)
        
        # Criar ou remover reação
        reaction, created = InternalChatReaction.objects.get_or_create(
            message=message,
            user=user,
            emoji=emoji
        )
        
        if not created:
            reaction.delete()
            action_type = 'reaction_removed'
        else:
            action_type = 'reaction_added'
        
        # Notificar via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"internal_chat_{message.room.id}",
            {
                'type': action_type,
                'message_id': message.id,
                'user_id': user.id,
                'emoji': emoji
            }
        )
        
        return Response({'message': f'Reação {emoji} {"adicionada" if created else "removida"}'})

class InternalChatParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para participantes do chat
    """
    serializer_class = InternalChatParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        if not room_id:
            return InternalChatParticipant.objects.none()
        
        return InternalChatParticipant.objects.filter(
            room_id=room_id,
            is_active=True
        ).select_related('user')


class InternalChatUnreadCountView(APIView):
    """
    API para buscar contador total de mensagens não lidas do chat interno
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            # Buscar provedor do usuário
            provedor = getattr(user, 'provedor', None) or user.provedores_admin.first()
            
            if not provedor:
                return Response({'total_unread': 0})
            
            # Buscar salas onde o usuário participa
            user_rooms = InternalChatRoom.objects.filter(
                provedor=provedor,
                participants__user=user,
                participants__is_active=True,
                is_active=True
            )
            
            # Contar mensagens não lidas em todas as salas
            total_unread = 0
            for room in user_rooms:
                unread_count = room.messages.exclude(
                    read_receipts__user=user
                ).exclude(
                    sender=user
                ).count()
                total_unread += unread_count
            
            return Response({'total_unread': total_unread})
            
        except Exception as e:
            print(f"Erro na InternalChatUnreadCountView: {e}")
            return Response({'total_unread': 0})


class InternalChatUnreadByUserView(APIView):
    """
    API para buscar contadores de mensagens não lidas do chat interno por usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            # Buscar provedor do usuário
            provedor = getattr(user, 'provedor', None) or user.provedores_admin.first()
            
            if not provedor:
                return Response({})
            
            # Buscar salas onde o usuário participa
            user_rooms = InternalChatRoom.objects.filter(
                provedor=provedor,
                participants__user=user,
                participants__is_active=True,
                is_active=True
            )
            
            # Contar mensagens não lidas por remetente
            unread_by_sender = {}
            for room in user_rooms:
                # Buscar mensagens não lidas agrupadas por remetente
                unread_messages = room.messages.exclude(
                    read_receipts__user=user
                ).exclude(
                    sender=user
                ).values('sender').annotate(
                    count=Count('id')
                )
                
                for item in unread_messages:
                    sender_id = item['sender']
                    count = item['count']
                    if sender_id in unread_by_sender:
                        unread_by_sender[sender_id] += count
                    else:
                        unread_by_sender[sender_id] = count
            
            return Response(unread_by_sender)
            
        except Exception as e:
            print(f"Erro na InternalChatUnreadByUserView: {e}")
            return Response({})