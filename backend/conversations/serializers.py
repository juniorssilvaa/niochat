from rest_framework import serializers
from .models import Contact, Inbox, Conversation, Message, Team, TeamMember, CSATFeedback, CSATRequest
from core.serializers import UserSerializer, LabelSerializer


class ContactSerializer(serializers.ModelSerializer):
    inbox = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'phone', 'avatar',
            'additional_attributes', 'provedor', 'created_at', 'updated_at', 'inbox'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_inbox(self, obj):
        # Buscar a conversa mais recente do contato
        latest_conversation = obj.conversations.order_by('-created_at').first()
        if latest_conversation and latest_conversation.inbox:
            return InboxSerializer(latest_conversation.inbox).data
        return None


class InboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inbox
        fields = [
            'id', 'name', 'channel_type', 'provedor',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    media_type = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'message_type',
            'media_type', 'file_url',
            'content', 'is_from_customer', 'created_at', 'external_id', 'additional_attributes'
        ]
        read_only_fields = ['id', 'created_at']

    def get_media_type(self, obj):
        # Garante que sempre retorna o tipo de mídia correto
        return obj.message_type

    def get_file_url(self, obj):
        # Priorizar campo file_url direto do modelo
        if obj.file_url:
            return obj.file_url
            
        # Fallback para buscar nos atributos adicionais (retrocompatibilidade)
        if obj.additional_attributes:
            # Priorizar URL local se disponível
            local_url = obj.additional_attributes.get('local_file_url')
            if local_url:
                return local_url
            
            # Fallback para URL original
            return obj.additional_attributes.get('file_url')
        return None

    def create(self, validated_data):
        validated_data['is_from_customer'] = False
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    # Para criação, usamos IDs simples
    contact_id = serializers.IntegerField(write_only=True, required=False)
    inbox_id = serializers.IntegerField(write_only=True, required=False)
    assignee_id = serializers.IntegerField(write_only=True, required=False)
    
    # Para leitura, usamos objetos completos
    contact = ContactSerializer(read_only=True)
    inbox = InboxSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    
    # Garantir que additional_attributes seja writeable
    additional_attributes = serializers.JSONField(required=False)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'contact', 'inbox', 'assignee', 'status',
            'contact_id', 'inbox_id', 'assignee_id',
            'labels', 'additional_attributes',
            'last_message_at', 'created_at', 'messages'
        ]
        read_only_fields = ['id', 'last_message_at', 'created_at']
    
    def create(self, validated_data):
        # Extrair os campos _id mas manter no validated_data com nome correto
        contact_id = validated_data.pop('contact_id', None)
        inbox_id = validated_data.pop('inbox_id', None)
        assignee_id = validated_data.pop('assignee_id', None)
        
        # Buscar as instâncias dos objetos relacionados
        if contact_id:
            from .models import Contact
            validated_data['contact'] = Contact.objects.get(id=contact_id)
        if inbox_id:
            from .models import Inbox
            validated_data['inbox'] = Inbox.objects.get(id=inbox_id)
        if assignee_id:
            from core.models import User
            validated_data['assignee'] = User.objects.get(id=assignee_id)
            
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        print(f"🔍 DEBUG ConversationSerializer.update")
        print(f"    validated_data: {validated_data}")
        print(f"    instance.id: {instance.id}")
        
        # Extrair os campos _id se presentes
        contact_id = validated_data.pop('contact_id', None)
        inbox_id = validated_data.pop('inbox_id', None)
        assignee_id = validated_data.pop('assignee_id', None)
        
        # Atualizar as instâncias dos objetos relacionados se fornecidos
        if contact_id is not None:
            from .models import Contact
            validated_data['contact'] = Contact.objects.get(id=contact_id) if contact_id else None
        if inbox_id is not None:
            from .models import Inbox
            validated_data['inbox'] = Inbox.objects.get(id=inbox_id) if inbox_id else None
        if assignee_id is not None:
            from core.models import User
            validated_data['assignee'] = User.objects.get(id=assignee_id) if assignee_id else None
        
        # Garantir que additional_attributes seja atualizado corretamente
        if 'additional_attributes' in validated_data:
            instance.additional_attributes = validated_data['additional_attributes']
            validated_data.pop('additional_attributes')  # Remove para evitar conflito
            
        # Atualizar outros campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de conversas, permitindo modificar assignee e status"""
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Conversation
        fields = ['assignee', 'assignee_id', 'status']
        read_only_fields = ['assignee']

    def update(self, instance, validated_data):
        # Suporte a assignee_id para facilitar PATCHs do frontend
        assignee_id = validated_data.pop('assignee_id', None)
        if assignee_id is not None:
            from core.models import User
            instance.assignee = User.objects.get(id=assignee_id) if assignee_id else None
        
        # Atualizar status se fornecido
        status_value = validated_data.get('status', None)
        if status_value is not None:
            instance.status = status_value
        
        instance.save()
        return instance


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de conversas"""
    contact = ContactSerializer(read_only=True)
    inbox = InboxSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'contact', 'inbox', 'assignee', 'status',
            'labels', 'additional_attributes', 'last_message_at', 'created_at',
            'last_message', 'unread_count'
        ]
        read_only_fields = ['id', 'last_message_at', 'created_at']
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        # Implementar lógica de contagem de mensagens não lidas
        return 0


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

class TeamSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True, read_only=True)
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'provedor', 'members',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'provedor']


class CSATFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer para feedbacks CSAT
    """
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone', read_only=True)
    contact_photo = serializers.SerializerMethodField()
    rating_display = serializers.CharField(source='get_emoji_rating_display', read_only=True)
    
    def get_contact_photo(self, obj):
        """
        Busca a foto do contato usando a API da Uazapi
        """
        try:
            from core.uazapi_client import UazapiClient
            import logging
            
            logger = logging.getLogger(__name__)
            
            # Verificar se é canal WhatsApp
            if obj.channel_type != 'whatsapp':
                return obj.contact.avatar  # Retorna avatar padrão se não for WhatsApp
            
            # Obter configurações do provedor
            config = obj.provedor.integracoes_externas
            if not config:
                logger.warning(f"No external integrations found for provider {obj.provedor.id}")
                return obj.contact.avatar
            
            whatsapp_url = config.get('whatsapp_url')
            whatsapp_token = config.get('whatsapp_token')
            whatsapp_instance = config.get('whatsapp_instance')
            
            if not whatsapp_url or not whatsapp_token or not whatsapp_instance:
                logger.warning(f"WhatsApp configuration incomplete for provider {obj.provedor.id}")
                return obj.contact.avatar
            
            # Criar cliente Uazapi
            uazapi_client = UazapiClient(
                base_url=whatsapp_url,
                token=whatsapp_token
            )
            
            # Buscar informações do contato
            contact_info = uazapi_client.get_contact_info(
                instance_id=whatsapp_instance,
                phone=obj.contact.phone
            )
            
            if contact_info and contact_info.get('image'):
                # Atualizar avatar do contato no banco para cache
                obj.contact.avatar = contact_info['image']
                obj.contact.save(update_fields=['avatar'])
                
                logger.info(f"Updated contact {obj.contact.id} avatar from Uazapi")
                return contact_info['image']
            else:
                logger.info(f"No profile picture found for contact {obj.contact.phone}")
                return obj.contact.avatar
                
        except Exception as e:
            logger.error(f"Error fetching contact photo from Uazapi: {e}")
            return obj.contact.avatar  # Fallback para avatar padrão
    
    class Meta:
        model = CSATFeedback
        fields = [
            'id', 'conversation', 'contact', 'contact_name', 'contact_phone', 'contact_photo',
            'emoji_rating', 'rating_value', 'rating_display', 'channel_type',
            'feedback_sent_at', 'conversation_ended_at', 'response_time_minutes',
            'original_message', 'additional_data'
        ]
        read_only_fields = [
            'id', 'feedback_sent_at', 'contact_name', 'contact_phone', 'rating_display'
        ]


class CSATRequestSerializer(serializers.ModelSerializer):
    """
    Serializer para solicitações de CSAT
    """
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CSATRequest
        fields = [
            'id', 'conversation', 'contact', 'contact_name', 'contact_phone',
            'status', 'status_display', 'conversation_ended_at', 'scheduled_send_at',
            'sent_at', 'responded_at', 'channel_type', 'csat_feedback',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'contact_name', 'contact_phone', 'status_display',
            'created_at', 'updated_at'
        ]


class CSATStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas do dashboard CSAT
    """
    total_feedbacks = serializers.IntegerField()
    average_rating = serializers.FloatField()
    satisfaction_rate = serializers.FloatField()
    rating_distribution = serializers.ListField()
    channel_distribution = serializers.ListField()
    daily_stats = serializers.ListField()
    recent_feedbacks = CSATFeedbackSerializer(many=True, read_only=True)

