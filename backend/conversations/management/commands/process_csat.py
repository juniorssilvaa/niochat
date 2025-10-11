from django.core.management.base import BaseCommand
from django.utils import timezone
from conversations.models import CSATRequest
from conversations.csat_automation import CSATAutomationService
import pytz

class Command(BaseCommand):
    help = 'Processa CSAT requests pendentes que já deveriam ter sido enviados'

    def handle(self, *args, **options):
        sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
        now = timezone.now().astimezone(sao_paulo_tz)
        
        self.stdout.write(f'Verificando CSATs pendentes às {now}')
        
        # Buscar CSATs pendentes que já deveriam ter sido enviados
        pending_csats = CSATRequest.objects.filter(status='pending')
        
        processed = 0
        for csat_request in pending_csats:
            if csat_request.scheduled_send_at:
                scheduled_local = csat_request.scheduled_send_at.astimezone(sao_paulo_tz)
                if now > scheduled_local:
                    self.stdout.write(f'Processando CSAT {csat_request.id} (agendado para {scheduled_local})')
                    try:
                        result = CSATAutomationService.send_csat_message(csat_request.id)
                        if result:
                            self.stdout.write(self.style.SUCCESS(f'✅ CSAT {csat_request.id} enviado com sucesso'))
                            processed += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'❌ Falha ao enviar CSAT {csat_request.id}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'❌ Erro ao processar CSAT {csat_request.id}: {e}'))
                else:
                    self.stdout.write(f'⏳ CSAT {csat_request.id} ainda não é hora (agendado para {scheduled_local})')
        
        self.stdout.write(self.style.SUCCESS(f'Processados {processed} CSATs'))
