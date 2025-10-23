"""
Comando Django para executar análise de recuperação de conversas
"""
from django.core.management.base import BaseCommand
from conversations.recovery_service import ConversationRecoveryService
from core.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Executa análise de recuperação de conversas para todos os provedores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-id',
            type=int,
            help='ID do provedor específico (opcional)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=7,
            help='Quantos dias atrás analisar (padrão: 7)',
        )
        parser.add_argument(
            '--send-messages',
            action='store_true',
            help='Enviar mensagens de recuperação (padrão: apenas analisar)',
        )

    def handle(self, *args, **options):
        provider_id = options.get('provider_id')
        days_back = options.get('days_back', 7)
        send_messages = options.get('send_messages', False)
        
        recovery_service = ConversationRecoveryService()
        
        if provider_id:
            # Analisar provedor específico
            self.stdout.write(f'Analisando conversas do provedor {provider_id}...')
            self._process_provider(recovery_service, provider_id, days_back, send_messages)
        else:
            # Analisar todos os provedores
            from core.models import Provedor
            providers = Provedor.objects.filter(is_active=True)
            
            self.stdout.write(f'Analisando conversas de {len(providers)} provedores...')
            
            for provider in providers:
                self._process_provider(recovery_service, provider.id, days_back, send_messages)
        
        self.stdout.write(
            self.style.SUCCESS('Análise de recuperação concluída!')
        )

    def _process_provider(self, recovery_service, provider_id, days_back, send_messages):
        """Processa análise para um provedor específico"""
        try:
            if send_messages:
                # Executar campanha completa
                results = recovery_service.process_recovery_campaign(provider_id, days_back)
                
                self.stdout.write(
                    f'Provedor {provider_id}: '
                    f'{results["successful_sends"]} mensagens enviadas, '
                    f'{results["failed_sends"]} falhas'
                )
            else:
                # Apenas analisar
                candidates = recovery_service.analyze_provider_conversations(provider_id, days_back)
                
                self.stdout.write(
                    f'Provedor {provider_id}: {len(candidates)} candidatos encontrados'
                )
                
                for candidate in candidates[:5]:  # Mostrar apenas os primeiros 5
                    self.stdout.write(
                        f'  - {candidate["contact_name"]} ({candidate["contact_phone"]}): '
                        f'{candidate["recovery_reason"]}'
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao processar provedor {provider_id}: {e}')
            )
