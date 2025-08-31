"""
Views para funcionalidades CSAT (Customer Satisfaction Score)
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Provedor
from .models import CSATFeedback, CSATRequest, Conversation, Contact
from .serializers import CSATFeedbackSerializer, CSATRequestSerializer, CSATStatsSerializer
from .csat_service import CSATService

logger = logging.getLogger(__name__)


class CSATFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar feedbacks CSAT
    """
    serializer_class = CSATFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar por provedor do usuário
        user = self.request.user
        provedor = None
        
        # Tentar por provedor_id primeiro
        if hasattr(user, 'provedor_id') and user.provedor_id:
            provedor = Provedor.objects.filter(id=user.provedor_id).first()
        
        # Se não encontrou, tentar por relacionamento direto
        if not provedor and hasattr(user, 'provedor') and user.provedor:
            provedor = user.provedor
        
        # Se ainda não encontrou, tentar por admins
        if not provedor:
            provedor = Provedor.objects.filter(admins=user).first()
            
        if not provedor:
            return CSATFeedback.objects.none()
            
        return CSATFeedback.objects.filter(
            provedor=provedor
        ).select_related('contact', 'conversation').order_by('-feedback_sent_at')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint para obter estatísticas CSAT para o dashboard
        """
        try:
            # Obter parâmetros
            days = int(request.query_params.get('days', 30))
            
            # Buscar provedor
            user = request.user
            provedor = None
            
            # Tentar por provedor_id primeiro
            if hasattr(user, 'provedor_id') and user.provedor_id:
                provedor = Provedor.objects.filter(id=user.provedor_id).first()
            
            # Se não encontrou, tentar por relacionamento direto
            if not provedor and hasattr(user, 'provedor') and user.provedor:
                provedor = user.provedor
            
            # Se ainda não encontrou, tentar por admins
            if not provedor:
                provedor = Provedor.objects.filter(admins=user).first()
                
            if not provedor:
                return Response(
                    {'error': 'Provedor não encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obter estatísticas
            stats = CSATService.get_csat_stats(provedor, days)
            
            # Serializar recent_feedbacks separadamente
            if 'recent_feedbacks' in stats and stats['recent_feedbacks']:
                recent_feedbacks_serializer = CSATFeedbackSerializer(stats['recent_feedbacks'], many=True)
                stats['recent_feedbacks'] = recent_feedbacks_serializer.data
            else:
                stats['recent_feedbacks'] = []
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error getting CSAT stats: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Endpoint para obter feedbacks recentes
        """
        try:
            limit = int(request.query_params.get('limit', 10))
            
            feedbacks = self.get_queryset()[:limit]
            serializer = self.get_serializer(feedbacks, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting recent CSAT feedbacks: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CSATRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar solicitações de CSAT
    """
    serializer_class = CSATRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filtrar por provedor do usuário
        user = self.request.user
        provedor = None
        
        # Tentar por provedor_id primeiro
        if hasattr(user, 'provedor_id') and user.provedor_id:
            provedor = Provedor.objects.filter(id=user.provedor_id).first()
        
        # Se não encontrou, tentar por relacionamento direto
        if not provedor and hasattr(user, 'provedor') and user.provedor:
            provedor = user.provedor
        
        # Se ainda não encontrou, tentar por admins
        if not provedor:
            provedor = Provedor.objects.filter(admins=user).first()
            
        if not provedor:
            return CSATRequest.objects.none()
            
        return CSATRequest.objects.filter(
            provedor=provedor
        ).select_related('contact', 'conversation', 'csat_feedback').order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def manual_request(self, request):
        """
        Criar solicitação manual de CSAT para uma conversa
        """
        try:
            conversation_id = request.data.get('conversation_id')
            
            if not conversation_id:
                return Response(
                    {'error': 'ID da conversa é obrigatório'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar se a conversa existe e pertence ao provedor
            conversation = Conversation.objects.filter(
                id=conversation_id,
                inbox__provedor__in=Provedor.objects.filter(
                    Q(admins=request.user) | Q(atendentes=request.user)
                )
            ).first()
            
            if not conversation:
                return Response(
                    {'error': 'Conversa não encontrada'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Criar solicitação CSAT
            csat_request = CSATService.schedule_csat_request(
                conversation_id=conversation.id,
                ended_by_user_id=request.user.id
            )
            
            if csat_request:
                serializer = self.get_serializer(csat_request)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Erro ao criar solicitação CSAT'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error creating manual CSAT request: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def process_csat_webhook(request):
    """
    Webhook para processar mensagens de feedback CSAT
    Será chamado quando uma mensagem com emoji for recebida
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        data = request.data if hasattr(request, 'data') else {}
        
        # Extrair informações da mensagem
        message_content = data.get('message', '')
        contact_id = data.get('contact_id')
        conversation_id = data.get('conversation_id')
        
        if not all([message_content, contact_id, conversation_id]):
            return JsonResponse({'error': 'Dados incompletos'}, status=400)
        
        # Buscar contato e conversa
        try:
            contact = Contact.objects.get(id=contact_id)
            conversation = Conversation.objects.get(id=conversation_id)
        except (Contact.DoesNotExist, Conversation.DoesNotExist):
            return JsonResponse({'error': 'Contato ou conversa não encontrados'}, status=404)
        
        # Processar feedback CSAT
        csat_feedback = CSATService.process_csat_response(
            message_content=message_content,
            contact=contact,
            conversation=conversation
        )
        
        if csat_feedback:
            return JsonResponse({
                'success': True,
                'csat_feedback_id': csat_feedback.id,
                'rating': csat_feedback.emoji_rating,
                'rating_value': csat_feedback.rating_value
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum feedback CSAT detectado'
            })
            
    except Exception as e:
        logger.error(f"Error processing CSAT webhook: {str(e)}")
        return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
