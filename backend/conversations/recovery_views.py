"""
Views para Recuperação de Conversas
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from conversations.recovery_service import ConversationRecoveryService
from conversations.models import Conversation, RecoveryAttempt, RecoverySettings
from core.models import User

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recovery_stats(request):
    """
    Retorna estatísticas de recuperação de conversas
    """
    try:
        user = request.user
        
        # Verificar se o usuário tem provedores associados
        if not user.provedores_admin.exists():
            return Response(
                {'error': 'Usuário não possui provedores associados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar o primeiro provedor do usuário (ou implementar lógica para múltiplos)
        provider = user.provedores_admin.first()
        provider_id = provider.id
        
        # Buscar conversas dos últimos 30 dias
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=30)
        
        # Buscar estatísticas reais do banco de dados
        from .models import RecoveryAttempt
        
        # Buscar tentativas do provedor através das conversas
        recent_attempts = RecoveryAttempt.objects.filter(
            conversation__inbox__provedor_id=provider_id
        ).order_by('-sent_at')[:10]
        
        # Calcular estatísticas
        total_attempts = RecoveryAttempt.objects.filter(
            conversation__inbox__provedor_id=provider_id
        ).count()
        
        successful_recoveries = RecoveryAttempt.objects.filter(
            conversation__inbox__provedor_id=provider_id,
            status='recovered'
        ).count()
        
        pending_recoveries = RecoveryAttempt.objects.filter(
            conversation__inbox__provedor_id=provider_id,
            status__in=['pending', 'sent']
        ).count()
        
        conversion_rate = (successful_recoveries / total_attempts * 100) if total_attempts > 0 else 0
        
        recent_activities = []
        for attempt in recent_attempts:
            recent_activities.append({
                'id': attempt.id,
                'contact_name': attempt.conversation.contact.name if attempt.conversation.contact else 'N/A',
                'phone': attempt.conversation.contact.phone if attempt.conversation.contact else 'N/A',
                'status': attempt.status,
                'message_sent': attempt.status in ['sent', 'recovered'],
                'sent_at': attempt.sent_at.isoformat() if attempt.sent_at else None,
                'recovery_reason': attempt.additional_attributes.get('recovery_reason', 'N/A'),
                'attempt_number': attempt.attempt_number
            })
        
        # Estatísticas baseadas nos dados reais
        stats = {
            'total_attempts': total_attempts,
            'successful_recoveries': successful_recoveries,
            'pending_recoveries': pending_recoveries,
            'conversion_rate': conversion_rate,
            'recent_activities': recent_activities
        }
        
        # Retornar estrutura esperada pelo frontend
        return Response({
            'stats': stats,
            'conversations': recent_activities
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de recuperação: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_conversations(request):
    """
    Analisa conversas para identificar candidatos à recuperação
    """
    try:
        user = request.user
        
        # Verificar se o usuário tem provedores associados
        if not user.provedores_admin.exists():
            return Response(
                {'error': 'Usuário não possui provedores associados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar o primeiro provedor do usuário
        provider = user.provedores_admin.first()
        provider_id = provider.id
        
        days_back = request.data.get('days_back', 7)
        
        recovery_service = ConversationRecoveryService()
        candidates = recovery_service.analyze_provider_conversations(provider_id, days_back)
        
        
        return Response({
            'candidates_found': len(candidates),
            'candidates': candidates
        })
        
    except Exception as e:
        logger.error(f"Erro ao analisar conversas: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_recovery_campaign(request):
    """
    Envia campanha de recuperação para clientes identificados
    """
    try:
        user = request.user
        
        # Verificar se o usuário tem provedores associados
        if not user.provedores_admin.exists():
            return Response(
                {'error': 'Usuário não possui provedores associados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar o primeiro provedor do usuário
        provider = user.provedores_admin.first()
        provider_id = provider.id
        
        days_back = request.data.get('days_back', 7)
        
        recovery_service = ConversationRecoveryService()
        results = recovery_service.process_recovery_campaign(provider_id, days_back)
        
        return Response(results)
        
    except Exception as e:
        logger.error(f"Erro ao enviar campanha de recuperação: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recovery_settings(request):
    """
    Retorna configurações de recuperação
    """
    try:
        user = request.user
        
        # Verificar se o usuário tem provedores associados
        if not user.provedores_admin.exists():
            return Response(
                {'error': 'Usuário não possui provedores associados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar o primeiro provedor do usuário
        provider = user.provedores_admin.first()
        provider_id = provider.id
        
        # Buscar configurações reais do banco de dados
        try:
            recovery_settings = RecoverySettings.objects.get(provedor=provider)
            settings = {
                'recovery_enabled': recovery_settings.enabled,
                'max_attempts': recovery_settings.max_attempts,
                'delay_minutes': recovery_settings.delay_minutes,
                'auto_discount': recovery_settings.auto_discount,
                'discount_percentage': recovery_settings.discount_percentage,
                'keywords': recovery_settings.keywords,
                'created_at': recovery_settings.created_at.isoformat(),
                'updated_at': recovery_settings.updated_at.isoformat()
            }
        except RecoverySettings.DoesNotExist:
            # Criar configurações padrão se não existirem
            recovery_settings = RecoverySettings.objects.create(
                provedor=provider,
                enabled=True,
                delay_minutes=30,
                max_attempts=3,
                auto_discount=False,
                discount_percentage=10,
                keywords=['plano', 'internet', 'velocidade', 'preço']
            )
            settings = {
                'recovery_enabled': recovery_settings.enabled,
                'max_attempts': recovery_settings.max_attempts,
                'delay_minutes': recovery_settings.delay_minutes,
                'auto_discount': recovery_settings.auto_discount,
                'discount_percentage': recovery_settings.discount_percentage,
                'keywords': recovery_settings.keywords,
                'created_at': recovery_settings.created_at.isoformat(),
                'updated_at': recovery_settings.updated_at.isoformat()
            }
        
        return Response(settings)
        
    except Exception as e:
        logger.error(f"Erro ao buscar configurações de recuperação: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_recovery_settings(request):
    """
    Atualiza configurações de recuperação
    """
    try:
        user = request.user
        
        # Verificar se o usuário tem provedores associados
        if not user.provedores_admin.exists():
            return Response(
                {'error': 'Usuário não possui provedores associados'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar o primeiro provedor do usuário
        provider = user.provedores_admin.first()
        provider_id = provider.id
        
        # Salvar configurações no banco de dados
        try:
            recovery_settings, created = RecoverySettings.objects.get_or_create(
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
            
            # Atualizar com os dados recebidos
            recovery_settings.enabled = request.data.get('recovery_enabled', recovery_settings.enabled)
            recovery_settings.max_attempts = request.data.get('max_attempts', recovery_settings.max_attempts)
            recovery_settings.delay_minutes = request.data.get('delay_minutes', recovery_settings.delay_minutes)
            recovery_settings.auto_discount = request.data.get('auto_discount', recovery_settings.auto_discount)
            recovery_settings.discount_percentage = request.data.get('discount_percentage', recovery_settings.discount_percentage)
            recovery_settings.keywords = request.data.get('keywords', recovery_settings.keywords)
            recovery_settings.save()
            
            return Response({
                'message': 'Configurações atualizadas com sucesso',
                'settings': {
                    'recovery_enabled': recovery_settings.enabled,
                    'max_attempts': recovery_settings.max_attempts,
                    'delay_minutes': recovery_settings.delay_minutes,
                    'auto_discount': recovery_settings.auto_discount,
                    'discount_percentage': recovery_settings.discount_percentage,
                    'keywords': recovery_settings.keywords,
                    'updated_at': recovery_settings.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return Response(
                {'error': 'Erro ao salvar configurações'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações de recuperação: {e}")
        return Response(
            {'error': 'Erro interno do servidor'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
