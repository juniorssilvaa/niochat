#!/usr/bin/env python3
"""
Script para verificar dados do dashboard
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from conversations.models import Conversation, CSATFeedback
from core.models import Provedor

def main():
    print("=== VERIFICAÇÃO DOS DADOS DO DASHBOARD ===\n")
    
    # Verificar provedor
    provedor = Provedor.objects.first()
    if not provedor:
        print("❌ Nenhum provedor encontrado")
        return
    
    print(f"✅ Provedor: {provedor.nome}")
    
    # Verificar conversas
    conversas = Conversation.objects.filter(inbox__provedor=provedor)
    total_conversas = conversas.count()
    print(f"\n📊 CONVERSAS:")
    print(f"   Total: {total_conversas}")
    
    # Status das conversas
    for status in ['open', 'pending', 'closed', 'snoozed']:
        count = conversas.filter(status=status).count()
        print(f"   {status}: {count}")
    
    # Taxa de resolução
    resolvidas = conversas.filter(status='closed').count()
    taxa = (resolvidas / total_conversas * 100) if total_conversas > 0 else 0
    print(f"\n📈 TAXA DE RESOLUÇÃO:")
    print(f"   Resolvidas: {resolvidas}")
    print(f"   Taxa: {taxa:.1f}%")
    
    # CSAT
    feedbacks = CSATFeedback.objects.filter(provedor=provedor)
    total_csat = feedbacks.count()
    print(f"\n😊 CSAT:")
    print(f"   Total feedbacks: {total_csat}")
    
    if total_csat > 0:
        # Média dos ratings
        from django.db.models import Avg
        media = feedbacks.aggregate(avg=Avg('rating_value'))['avg'] or 0
        print(f"   Média: {media:.1f}")
        
        # Distribuição
        for rating in range(1, 6):
            count = feedbacks.filter(rating_value=rating).count()
            print(f"   Rating {rating}: {count}")
    
    # Verificar se há dados suficientes para mostrar no dashboard
    print(f"\n🎯 DASHBOARD:")
    if total_conversas == 0:
        print("   ❌ Sem conversas - dashboard vazio")
    else:
        print("   ✅ Tem conversas")
    
    if total_csat == 0:
        print("   ❌ Sem CSAT - satisfação média será 0.0")
    else:
        print("   ✅ Tem CSAT - satisfação média será calculada")
    
    if resolvidas == 0:
        print("   ❌ Sem conversas resolvidas - taxa de resolução será 0%")
    else:
        print("   ✅ Tem conversas resolvidas - taxa será calculada")

if __name__ == "__main__":
    main()



