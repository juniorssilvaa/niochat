from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from core.models import Provedor


class Contact(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, default='')
    email = models.EmailField(blank=True, null=True)
    avatar = models.URLField(blank=True, null=True, help_text="URL da foto do perfil do WhatsApp")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='contacts', null=True, blank=True)
    additional_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        unique_together = ['phone', 'provedor']


class Inbox(models.Model):
    name = models.CharField(max_length=255)
    channel_type = models.CharField(max_length=50)  # whatsapp, telegram, email, etc.
    channel_id = models.CharField(max_length=255, default='default')
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='inboxes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    additional_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.channel_type})"


class Conversation(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aberta'),
        ('closed', 'Fechada'),
        ('pending', 'Pendente'),
    ]
    
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='conversations')
    inbox = models.ForeignKey(Inbox, on_delete=models.CASCADE, related_name='conversations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_conversations')
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations', verbose_name='Equipe')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    additional_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Conversa com {self.contact.name}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('document', 'Documento'),
        ('location', 'Localização'),
        ('ptt', 'Mensagem de Voz'),
        ('sticker', 'Figurinha'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    is_from_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Arquivos de mídia
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # em bytes
    
    additional_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Mensagem de {self.conversation.contact.name}"


class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='teams', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('leader', 'Líder'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['team', 'user']

    def __str__(self):
        return f"{self.user.username} em {self.team.name}"


class RecoverySettings(models.Model):
    """Configurações do recuperador de conversas"""
    provedor = models.OneToOneField(Provedor, on_delete=models.CASCADE, related_name='recovery_settings')
    enabled = models.BooleanField(default=True)
    delay_minutes = models.IntegerField(default=30, help_text="Delay em minutos antes de tentar recuperar")
    max_attempts = models.IntegerField(default=3, help_text="Número máximo de tentativas")
    auto_discount = models.BooleanField(default=False, help_text="Aplicar desconto automático")
    discount_percentage = models.IntegerField(default=10, help_text="Percentual de desconto")
    keywords = models.JSONField(default=list, help_text="Palavras-chave para identificar interesse em planos")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configurações de recuperação - {self.provedor.name}"


class RecoveryAttempt(models.Model):
    """Registro de tentativas de recuperação"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviada'),
        ('recovered', 'Recuperada'),
        ('failed', 'Falhou'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='recovery_attempts')
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message_sent = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    response_received_at = models.DateTimeField(null=True, blank=True)
    potential_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    additional_attributes = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Tentativa {self.attempt_number} - {self.conversation.contact.name}"

    class Meta:
        unique_together = ['conversation', 'attempt_number']


# ===== CHAT INTERNO PARA ATENDENTES =====

class InternalChatRoom(models.Model):
    """
    Sala de chat interno para atendentes do provedor
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='chat_rooms')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # Tipos de sala
    ROOM_TYPES = [
        ('general', 'Geral'),
        ('support', 'Suporte'),
        ('sales', 'Vendas'), 
        ('private', 'Privado'),
        ('team', 'Equipe')
    ]
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='general')
    
    class Meta:
        db_table = 'internal_chat_rooms'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} - {self.provedor.nome}"

class InternalChatParticipant(models.Model):
    """
    Participantes da sala de chat
    """
    room = models.ForeignKey(InternalChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'internal_chat_participants'
        unique_together = ['room', 'user']
        
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"

class InternalChatMessage(models.Model):
    """
    Mensagens do chat interno
    """
    room = models.ForeignKey(InternalChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tipos de mensagem
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('file', 'Arquivo'),
        ('system', 'Sistema')
    ]
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Arquivos de mídia
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # em bytes
    
    # Reply/Thread
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Status da mensagem
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Metadados adicionais
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'internal_chat_messages'
        ordering = ['created_at']
        
    def __str__(self):
        content_preview = self.content[:50] if self.content else f"[{self.message_type}]"
        return f"{self.sender.username}: {content_preview}"

class InternalChatMessageRead(models.Model):
    """
    Controle de mensagens lidas por usuário
    """
    message = models.ForeignKey(InternalChatMessage, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'internal_chat_message_reads'
        unique_together = ['message', 'user']
        
    def __str__(self):
        return f"{self.user.username} read message {self.message.id}"

class InternalChatReaction(models.Model):
    """
    Reações às mensagens (emojis)
    """
    message = models.ForeignKey(InternalChatMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # 👍, ❤️, 😂, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'internal_chat_reactions'
        unique_together = ['message', 'user', 'emoji']
        
    def __str__(self):
        return f"{self.user.username} {self.emoji} on message {self.message.id}"


# ===== CHAT PRIVADO ENTRE USUÁRIOS =====

class PrivateMessage(models.Model):
    """
    Mensagens privadas entre dois usuários
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_private_messages')
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tipos de mensagem
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('file', 'Arquivo'),
        ('system', 'Sistema')
    ]
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Arquivos de mídia
    file_url = models.URLField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # em bytes
    
    # Reply/Thread
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Status da mensagem
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Isolamento por provedor
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='private_messages')
    
    # Metadados adicionais
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'private_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient', 'provedor']),
            models.Index(fields=['recipient', 'is_read']),
        ]
        
    def __str__(self):
        content_preview = self.content[:50] if self.content else f"[{self.message_type}]"
        return f"{self.sender.username} -> {self.recipient.username}: {content_preview}"
    
    def mark_as_read(self):
        """Marcar mensagem como lida"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

class PrivateMessageReaction(models.Model):
    """
    Reações às mensagens privadas (emojis)
    """
    message = models.ForeignKey(PrivateMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  # 👍, ❤️, 😂, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'private_message_reactions'
        unique_together = ['message', 'user', 'emoji']
        
    def __str__(self):
        return f"{self.user.username} {self.emoji} on private message {self.message.id}"


class CSATFeedback(models.Model):
    """
    Modelo para armazenar feedbacks CSAT dos clientes
    """
    EMOJI_RATINGS = [
        ('😡', 'Muito insatisfeito - 1'),
        ('😕', 'Insatisfeito - 2'), 
        ('😐', 'Neutro - 3'),
        ('🙂', 'Satisfeito - 4'),
        ('🤩', 'Muito satisfeito - 5'),
    ]
    
    RATING_VALUES = {
        '😡': 1,
        '😕': 2, 
        '😐': 3,
        '🙂': 4,
        '🤩': 5,
    }
    
    # Relacionamentos
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='csat_feedbacks')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='csat_feedbacks') 
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='csat_feedbacks')
    
    # Dados do feedback
    emoji_rating = models.CharField(max_length=10, choices=EMOJI_RATINGS)
    rating_value = models.IntegerField()  # 1-5 baseado no emoji
    channel_type = models.CharField(max_length=20)  # whatsapp, telegram, email, etc
    
    # Metadados
    feedback_sent_at = models.DateTimeField(auto_now_add=True)
    conversation_ended_at = models.DateTimeField()
    response_time_minutes = models.IntegerField()  # Tempo entre fim da conversa e resposta
    
    # Dados adicionais para auditoria
    original_message = models.TextField(blank=True, null=True)  # Mensagem original do cliente
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'csat_feedbacks'
        ordering = ['-feedback_sent_at']
        indexes = [
            models.Index(fields=['provedor', 'feedback_sent_at']),
            models.Index(fields=['provedor', 'rating_value']),
            models.Index(fields=['channel_type', 'provedor']),
        ]
        
    def __str__(self):
        return f"CSAT {self.emoji_rating} ({self.rating_value}) - {self.contact} - {self.feedback_sent_at.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        # Automaticamente definir rating_value baseado no emoji
        if self.emoji_rating and not self.rating_value:
            self.rating_value = self.RATING_VALUES.get(self.emoji_rating, 3)
        super().save(*args, **kwargs)


class CSATRequest(models.Model):
    """
    Modelo para controlar as solicitações de CSAT enviadas
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('sent', 'Enviado'),
        ('responded', 'Respondido'),
        ('expired', 'Expirado'),
    ]
    
    # Relacionamentos
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='csat_requests')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='csat_requests')
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='csat_requests')
    
    # Status e timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    conversation_ended_at = models.DateTimeField()
    scheduled_send_at = models.DateTimeField()  # 2 minutos após encerramento
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Referência ao feedback (quando respondido)
    csat_feedback = models.OneToOneField(CSATFeedback, on_delete=models.CASCADE, null=True, blank=True, related_name='request')
    
    # Metadados
    channel_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'csat_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provedor', 'status']),
            models.Index(fields=['scheduled_send_at', 'status']),
        ]
        
    def __str__(self):
        return f"CSAT Request - {self.contact} - {self.status} - {self.conversation_ended_at.strftime('%d/%m/%Y %H:%M')}"
