import logging
import json
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from conversations.models import Conversation, Message, Team, TeamMember
from core.models import Provedor
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class DatabaseTools:
    """
    Ferramentas seguras para a IA interagir com o banco de dados
    """
    
    def __init__(self, provedor: Provedor):
        self.provedor = provedor
        self.channel_layer = get_channel_layer()

    def buscar_equipes_disponíveis(self) -> Dict[str, Any]:
        """
        Tool: buscar_equipes_disponíveis
        Busca todas as equipes disponíveis no provedor atual
        """
        try:
            equipes = Team.objects.filter(
                provedor=self.provedor,
                is_active=True
            ).values('id', 'name', 'description')
            
            equipes_list = list(equipes)
            
            logger.info(f"Equipes encontradas para {self.provedor.nome}: {len(equipes_list)}")
            
            return {
                'success': True,
                'equipes': equipes_list,
                'total': len(equipes_list),
                'provedor': self.provedor.nome
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar equipes: {e}")
            return {
                'success': False,
                'erro': f"Erro ao buscar equipes: {str(e)}"
            }

    def buscar_membro_disponível_equipe(self, nome_equipe: str) -> Dict[str, Any]:
        """
        Tool: buscar_membro_disponível_equipe
        Busca um membro disponível de uma equipe específica
        
        Args:
            nome_equipe: Nome da equipe (SUPORTE, FINANCEIRO, ATENDIMENTO)
        """
        try:
            # Buscar equipe
            equipe = Team.objects.filter(
                provedor=self.provedor,
                name__icontains=nome_equipe,
                is_active=True
            ).first()
            
            if not equipe:
                return {
                    'success': False,
                    'erro': f'Equipe {nome_equipe} não encontrada ou inativa'
                }
            
            # Buscar membros da equipe
            membros = TeamMember.objects.filter(
                team=equipe
            ).select_related('user')
            
            if not membros.exists():
                return {
                    'success': False,
                    'erro': f'Nenhum membro ativo encontrado na equipe {nome_equipe}'
                }
            
            # Escolher primeiro membro disponível
            membro = membros.first()
            
            return {
                'success': True,
                'membro': {
                    'id': membro.user.id,
                    'nome': membro.user.get_full_name() or membro.user.username,
                    'username': membro.user.username,
                    'email': membro.user.email
                },
                'equipe': {
                    'id': equipe.id,
                    'name': equipe.name,
                    'description': equipe.description
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar membro da equipe: {e}")
            return {
                'success': False,
                'erro': f"Erro ao buscar membro da equipe: {str(e)}"
            }

    def analisar_conversa_para_transferencia(self, conversation_id: int) -> Dict[str, Any]:
        """
        Analisa a conversa para determinar a equipe mais adequada para transferência
        
        Args:
            conversation_id: ID da conversa a ser analisada
        
        Returns:
            Dict com análise e recomendação de equipe
        """
        try:
            # Buscar conversa
            conversa = Conversation.objects.filter(
                id=conversation_id,
                inbox__provedor=self.provedor
            ).first()
            
            if not conversa:
                return {
                    'success': False,
                    'erro': f'Conversa {conversation_id} não encontrada'
                }
            
            # Buscar últimas mensagens da conversa
            mensagens = Message.objects.filter(
                conversation=conversa
            ).order_by('-created_at')[:20]  # Últimas 20 mensagens
            
            # Analisar conteúdo das mensagens
            texto_completo = ""
            for msg in reversed(mensagens):  # Ordem cronológica
                if msg.content:
                    texto_completo += f" {msg.content.lower()}"
            
            # Palavras-chave para cada tipo de equipe
            palavras_suporte = [
                'internet', 'conexão', 'modem', 'roteador', 'sinal', 'velocidade', 'lenta', 'caiu', 
                'desconectou', 'problema', 'técnico', 'instalação', 'equipamento', 'cabo', 'fibra',
                'drop', 'led', 'vermelho', 'piscando', 'sem acesso', 'não funciona', 'erro',
                'chamado', 'suporte', 'técnico', 'reparo', 'manutenção'
            ]
            
            palavras_financeiro = [
                'fatura', 'boleto', 'pagamento', 'pagar', 'valor', 'preço', 'conta', 'débito',
                'vencimento', 'multa', 'juros', 'desconto', 'segunda via', 'comprovante',
                'recibo', 'parcelamento', 'cartão', 'pix', 'transferência', 'dinheiro',
                'cobrança', 'em aberto', 'atraso', 'suspenso'
            ]
            
            palavras_vendas = [
                'plano', 'contratar', 'contratação', 'oferta', 'melhor', 'escolher', 'novo',
                'mudar', 'alterar', 'preço', 'velocidade', 'instalação', 'endereço',
                'documentos', 'proposta', 'orçamento', 'promoção', 'desconto', 'vantagem'
            ]
            
            # Contar ocorrências
            score_suporte = sum(1 for palavra in palavras_suporte if palavra in texto_completo)
            score_financeiro = sum(1 for palavra in palavras_financeiro if palavra in texto_completo)
            score_vendas = sum(1 for palavra in palavras_vendas if palavra in texto_completo)
            
            # Determinar equipe recomendada
            scores = {
                'SUPORTE TÉCNICO': score_suporte,
                'FINANCEIRO': score_financeiro,
                'ATENDIMENTO': score_vendas
            }
            
            equipe_recomendada = max(scores, key=scores.get)
            score_maximo = scores[equipe_recomendada]
            
            # Verificar se há equipe disponível
            equipes_disponiveis = self.buscar_equipes_disponíveis()
            
            if not equipes_disponiveis['success']:
                return {
                    'success': False,
                    'erro': 'Não foi possível verificar equipes disponíveis'
                }
            
            # Verificar se a equipe recomendada existe
            equipe_existe = any(
                equipe['name'].upper() == equipe_recomendada.upper() 
                for equipe in equipes_disponiveis['equipes']
            )
            
            if not equipe_existe:
                # Se não existe, usar primeira equipe disponível
                if equipes_disponiveis['equipes']:
                    equipe_recomendada = equipes_disponiveis['equipes'][0]['name']
                else:
                    return {
                        'success': False,
                        'erro': 'Nenhuma equipe disponível encontrada'
                    }
            
            return {
                'success': True,
                'conversa_id': conversation_id,
                'equipe_recomendada': equipe_recomendada,
                'score_maximo': score_maximo,
                'scores': scores,
                'confianca': 'alta' if score_maximo >= 3 else 'media' if score_maximo >= 1 else 'baixa',
                'motivo': self._gerar_motivo_transferencia(equipe_recomendada, scores),
                'equipes_disponiveis': equipes_disponiveis['equipes']
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar conversa para transferência: {e}")
            return {
                'success': False,
                'erro': f"Erro ao analisar conversa: {str(e)}"
            }

    def _gerar_motivo_transferencia(self, equipe: str, scores: Dict[str, int]) -> str:
        """Gera motivo da transferência baseado na análise"""
        if equipe == 'SUPORTE TÉCNICO':
            return "Problema técnico identificado - transferindo para equipe de suporte"
        elif equipe == 'FINANCEIRO':
            return "Questão financeira identificada - transferindo para equipe financeira"
        elif equipe == 'ATENDIMENTO':
            return "Solicitação de atendimento geral - transferindo para equipe de atendimento"
        else:
            return f"Transferência para {equipe} - análise automática da conversa"

    def transferir_conversa_inteligente(self, conversation_id: int) -> Dict[str, Any]:
        """
        Executa transferência inteligente baseada na análise da conversa
        
        Args:
            conversation_id: ID da conversa
        
        Returns:
            Dict com resultado da transferência
        """
        try:
            # Analisar conversa
            analise = self.analisar_conversa_para_transferencia(conversation_id)
            
            if not analise['success']:
                return analise
            
            # Executar transferência
            resultado = self.executar_transferencia_conversa(
                conversation_id=conversation_id,
                equipe_nome=analise['equipe_recomendada'],
                motivo=analise['motivo']
            )
            
            if resultado['success']:
                resultado['analise'] = analise
                resultado['transferencia_inteligente'] = True
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na transferência inteligente: {e}")
            return {
                'success': False,
                'erro': f"Erro na transferência inteligente: {str(e)}"
            }

    def executar_transferencia_conversa(self, conversation_id: int, equipe_nome: str, motivo: str) -> Dict[str, Any]:
        """
        Tool: executar_transferencia_conversa
        Transfere uma conversa para uma equipe específica
        
        Args:
            conversation_id: ID da conversa
            equipe_nome: Nome da equipe de destino
            motivo: Motivo da transferência
        """
        try:
            with transaction.atomic():
                # Buscar conversa com lock
                conversa = Conversation.objects.select_for_update().filter(
                    id=conversation_id,
                    inbox__provedor=self.provedor  # Segurança: apenas conversas do provedor
                ).first()
                
                if not conversa:
                    return {
                        'success': False,
                        'erro': f'Conversa {conversation_id} não encontrada ou sem permissão'
                    }
                
                # Buscar membro da equipe
                resultado_membro = self.buscar_membro_disponível_equipe(equipe_nome)
                
                if not resultado_membro['success']:
                    return resultado_membro
                
                membro_data = resultado_membro['membro']
                equipe_data = resultado_membro['equipe']
                
                # Executar transferência
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                membro_usuario = User.objects.get(id=membro_data['id'])
                
                status_anterior = conversa.status
                assignee_anterior = conversa.assignee
                
                # IMPORTANTE: Não atribuir diretamente ao membro, deixar em espera
                conversa.assignee = None  # Sem atribuição direta
                conversa.status = 'pending'  # Em Espera
                
                # Salvar informação da equipe nos additional_attributes
                if not conversa.additional_attributes:
                    conversa.additional_attributes = {}
                conversa.additional_attributes['assigned_team'] = {
                    'id': equipe_data['id'],
                    'name': equipe_data['name']
                }
                conversa.additional_attributes['transfer_motivo'] = motivo
                conversa.additional_attributes['transfer_timestamp'] = str(timezone.now())
                
                conversa.save()
                
                # Enviar notificação WebSocket
                if self.channel_layer:
                    async_to_sync(self.channel_layer.group_send)(
                        f"painel_{self.provedor.id}",
                        {
                            'type': 'conversation_status_changed',
                            'conversation': {
                                'id': conversa.id,
                                'status': conversa.status,
                                'assigned_team': equipe_data['name'],
                                'contact': {
                                    'name': conversa.contact.name,
                                    'phone': conversa.contact.phone
                                }
                            },
                            'message': f'Conversa transferida para {equipe_nome} - Status: Em Espera'
                        }
                    )
                
                logger.info(f"Transferência executada: Conversa {conversation_id} → {equipe_nome} (Status: Em Espera)")
                
                return {
                    'success': True,
                    'transferencia_realizada': True,
                    'conversa_id': conversa.id,
                    'status_anterior': status_anterior,
                    'status_atual': conversa.status,
                    'equipe_destino': equipe_nome,
                    'motivo': motivo,
                    'em_espera': True
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar transferência: {e}")
            return {
                'success': False,
                'erro': f"Erro ao executar transferência: {str(e)}"
            }

    def buscar_conversas_ativas(self) -> Dict[str, Any]:
        """
        Tool: buscar_conversas_ativas
        Busca todas as conversas ativas do provedor
        """
        try:
            conversas = Conversation.objects.filter(
                inbox__provedor=self.provedor
            ).select_related('contact', 'assignee', 'inbox').order_by('-last_message_at')
            
            conversas_data = []
            for conversa in conversas:
                conversas_data.append({
                    'id': conversa.id,
                    'status': conversa.status,
                    'contact_name': conversa.contact.name,
                    'contact_phone': conversa.contact.phone,
                    'assignee': conversa.assignee.get_full_name() if conversa.assignee else None,
                    'last_message_at': conversa.last_message_at.isoformat() if conversa.last_message_at else None,
                    'created_at': conversa.created_at.isoformat()
                })
            
            return {
                'success': True,
                'conversas': conversas_data,
                'total': len(conversas_data),
                'provedor': self.provedor.nome
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar conversas ativas: {e}")
            return {
                'success': False,
                'erro': f"Erro ao buscar conversas ativas: {str(e)}"
            }

    def buscar_estatisticas_atendimento(self) -> Dict[str, Any]:
        """
        Tool: buscar_estatisticas_atendimento
        Busca estatísticas gerais de atendimento do provedor
        """
        try:
            # Estatísticas básicas
            total_conversas = Conversation.objects.filter(inbox__provedor=self.provedor).count()
            
            conversas_abertas = Conversation.objects.filter(
                inbox__provedor=self.provedor,
                status='open'
            ).count()
            
            conversas_pendentes = Conversation.objects.filter(
                inbox__provedor=self.provedor,
                status='pending'
            ).count()
            
            conversas_com_ia = Conversation.objects.filter(
                inbox__provedor=self.provedor,
                status='snoozed'
            ).count()
            
            # Estatísticas por equipe
            equipes_stats = {}
            for team in Team.objects.filter(provedor=self.provedor, is_active=True):
                conversas_equipe = Conversation.objects.filter(
                    inbox__provedor=self.provedor,
                    additional_attributes__assigned_team__id=team.id
                ).count()
                
                equipes_stats[team.name] = {
                    'total_conversas': conversas_equipe,
                    'membros_ativos': team.members.count()
                }
            
            return {
                'success': True,
                'estatisticas_gerais': {
                    'total_conversas': total_conversas,
                    'conversas_abertas': conversas_abertas,
                    'conversas_pendentes': conversas_pendentes,
                    'conversas_com_ia': conversas_com_ia
                },
                'estatisticas_equipes': equipes_stats,
                'consultado_em': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {
                'success': False,
                'erro': f"Erro ao consultar estatísticas: {str(e)}"
            }

# Factory function para criar instância das ferramentas
def create_database_tools(provedor: Provedor) -> DatabaseTools:
    """Cria instância das ferramentas de banco para um provedor específico"""
    return DatabaseTools(provedor)





