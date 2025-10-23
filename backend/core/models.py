from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model

# Modelo User personalizado
class User(AbstractUser):
    USER_TYPES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador da Empresa'),
        ('agent', 'Atendente'),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='agent',
        verbose_name='Tipo de Usuário'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Avatar'
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Telefone'
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name='Online'
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Visualização'
    )
    permissions = models.JSONField(
        blank=True,
        default=list,
        verbose_name='Permissões Específicas'
    )
    # Preferências de som por usuário
    sound_notifications_enabled = models.BooleanField(
        default=False,
        verbose_name='Notificações Sonoras Ativas'
    )
    new_message_sound = models.CharField(
        max_length=200,
        default='mixkit-bell-notification-933.wav',
        verbose_name='Som para Novas Mensagens'
    )
    new_conversation_sound = models.CharField(
        max_length=200,
        default='mixkit-digital-quick-tone-2866.wav',
        verbose_name='Som para Novas Conversas'
    )
    session_timeout = models.IntegerField(
        default=30,
        verbose_name='Timeout da Sessão (minutos)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username


class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome da Empresa')
    slug = models.SlugField(unique=True, verbose_name='Slug')
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name='Logo')
    description = models.TextField(null=True, blank=True, verbose_name='Descrição')
    website = models.URLField(null=True, blank=True, verbose_name='Website')
    email = models.EmailField(null=True, blank=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefone')
    address = models.TextField(null=True, blank=True, verbose_name='Endereço')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']

    def __str__(self):
        return self.name


class CompanyUser(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador da Empresa'),
        ('agent', 'Atendente'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_users')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent', verbose_name='Função')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuário da Empresa'
        verbose_name_plural = 'Usuários da Empresa'
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"


class Provedor(models.Model):
    nome = models.CharField(max_length=200)
    site_oficial = models.URLField(null=True, blank=True)
    endereco = models.CharField(max_length=300, null=True, blank=True)
    redes_sociais = models.JSONField(null=True, blank=True, help_text='Redes sociais da empresa')
    horarios_atendimento = models.TextField(null=True, blank=True, help_text='Horários de atendimento (texto ou JSON)')
    dias_atendimento = models.TextField(null=True, blank=True, help_text='Dias de atendimento (texto ou JSON)')
    planos = models.TextField(null=True, blank=True, help_text='Planos da empresa (texto ou JSON)')
    dados_adicionais = models.TextField(null=True, blank=True, help_text='FAQ, orientações, termos, políticas, etc')
    integracoes_externas = models.JSONField(null=True, blank=True, help_text='Dados de integração com SGP/URA: app, token, endpoints personalizados')
    nome_agente_ia = models.CharField(max_length=100, null=True, blank=True)
    estilo_personalidade = models.CharField(max_length=50, null=True, blank=True, help_text='Ex: Formal, Brincalhão, Educado')
    modo_falar = models.CharField(max_length=100, null=True, blank=True, help_text='Ex: Nordestino, Formal, Descontraído')
    uso_emojis = models.CharField(max_length=20, null=True, blank=True, help_text='sempre, ocasionalmente, nunca')
    personalidade = models.JSONField(null=True, blank=True, help_text='Personalidade avançada: vicios_linguagem, caracteristicas, principios, humor')
    personalidade_avancada = models.JSONField(null=True, blank=True, help_text='Campos: vicios_linguagem, caracteristicas, principios, humor')
    email_contato = models.EmailField(null=True, blank=True, help_text='E-mail de contato do provedor')
    taxa_adesao = models.CharField(max_length=100, null=True, blank=True, help_text='Taxa de adesão')
    multa_cancelamento = models.CharField(max_length=200, null=True, blank=True, help_text='Multa de cancelamento')
    tipo_conexao = models.CharField(max_length=100, null=True, blank=True, help_text='Tipo de conexão')
    prazo_instalacao = models.CharField(max_length=100, null=True, blank=True, help_text='Prazo de instalação')
    documentos_necessarios = models.TextField(null=True, blank=True, help_text='Documentos necessários para cadastro')
    planos_internet = models.TextField(null=True, blank=True, help_text='Planos de internet oferecidos')
    planos_descricao = models.TextField(null=True, blank=True, help_text='Descrição detalhada dos planos')
    avatar_agente = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admins = models.ManyToManyField(User, blank=True, help_text='Usuários administradores deste provedor', related_name='provedores_admin')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Provedor'
        verbose_name_plural = 'Provedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Label(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Cor', help_text='Cor em formato hexadecimal (ex: #007bff)')
    description = models.TextField(null=True, blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='labels', verbose_name='Empresa', null=True, blank=True)
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='labels', verbose_name='Provedor', null=True, blank=True)

    class Meta:
        verbose_name = 'Rótulo'
        verbose_name_plural = 'Rótulos'

    def __str__(self):
        return self.name


class SystemConfig(models.Model):
    key = models.CharField(max_length=255, unique=True, verbose_name='Chave', default='', blank=True)
    value = models.TextField(verbose_name='Valor', default='', blank=True)
    description = models.TextField(null=True, blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sgp_app = models.CharField(max_length=200, null=True, blank=True, verbose_name='SGP App')
    sgp_token = models.CharField(max_length=500, null=True, blank=True, verbose_name='SGP Token')
    sgp_url = models.URLField(null=True, blank=True, verbose_name='SGP URL')
    openai_api_key = models.CharField(max_length=255, null=True, blank=True, verbose_name='OpenAI API Key')

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."


class Canal(models.Model):
    TIPO_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('whatsapp_beta', 'WhatsApp Beta'),
        ('telegram', 'Telegram'),
        ('email', 'Email'),
        ('webchat', 'WebChat'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
    ]
    
    nome = models.CharField(max_length=100, default='')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='whatsapp')
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='canais')
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dados_extras = models.JSONField(default=dict, blank=True)
    verification_code = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    api_hash = models.CharField(max_length=500, null=True, blank=True, verbose_name='Hash da API')

    class Meta:
        verbose_name = 'Canal'
        verbose_name_plural = 'Canais'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.tipo})"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Criar'),
        ('edit', 'Editar'),
        ('delete', 'Deletar'),
        ('view', 'Visualizar'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
        ('transfer', 'Transferir'),
        ('close', 'Fechar'),
        ('open', 'Abrir'),
        ('assign', 'Atribuir'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuário')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='Ação')
    details = models.TextField(verbose_name='Detalhes', default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Endereço IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    provedor = models.ForeignKey(Provedor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Provedor')
    channel_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='Tipo de Canal')
    contact_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Nome do Contato')
    conversation_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='ID da Conversa')
    csat_rating = models.IntegerField(null=True, blank=True, verbose_name='Avaliação CSAT')

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} - {self.user} - {self.timestamp}"


class MensagemSistema(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Título', default='')
    conteudo = models.TextField(verbose_name='Conteúdo', default='')
    tipo = models.CharField(max_length=50, choices=[
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('success', 'Sucesso'),
    ], default='info', verbose_name='Tipo')
    ativa = models.BooleanField(default=True, verbose_name='Ativa')
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name='Data de Início')
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name='Data de Fim')
    provedor = models.ForeignKey(Provedor, on_delete=models.CASCADE, related_name='mensagens_sistema', null=True, blank=True, verbose_name='Provedor')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mensagem do Sistema'
        verbose_name_plural = 'Mensagens do Sistema'
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo

# Outros modelos existentes
class SystemVersion(models.Model):
    """Modelo para gerenciar versões do sistema"""
    
    VERSION_TYPES = [
        ('major', 'Major'),
        ('minor', 'Minor'), 
        ('patch', 'Patch'),
    ]
    
    CHANGE_TYPES = [
        ('feature', 'Nova Funcionalidade'),
        ('improvement', 'Melhoria'),
        ('fix', 'Correção'),
        ('security', 'Segurança'),
    ]
    
    version = models.CharField(max_length=20, unique=True, help_text="Ex: 2.1.5")
    version_type = models.CharField(max_length=10, choices=VERSION_TYPES, default='patch')
    title = models.CharField(max_length=200, help_text="Título da versão")
    release_date = models.DateField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-release_date', '-version']
        verbose_name = "Versão do Sistema"
        verbose_name_plural = "Versões do Sistema"
    
    def __str__(self):
        return f"v{self.version} - {self.title}"


class ChangelogEntry(models.Model):
    """Entradas do changelog para cada versão"""
    
    version = models.ForeignKey(SystemVersion, on_delete=models.CASCADE, related_name='changes')
    change_type = models.CharField(max_length=15, choices=SystemVersion.CHANGE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0, help_text="Ordem de exibição")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Entrada do Changelog"
        verbose_name_plural = "Entradas do Changelog"
    
    def __str__(self):
        return f"{self.get_change_type_display()}: {self.title}"