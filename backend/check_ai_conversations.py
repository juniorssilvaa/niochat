#!/usr/bin/env python3
"""
Script para verificar conversas com IA
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from conversations.models import Conversation
from django.db import models

def check_ai_conversations():
    print("=== VERIFICANDO CONVERSAS COM IA ===\n")
    
    # Buscar conversas com status snoozed (IA)
    convs = Conversation.objects.filter(status='snoozed')
    print(f"✅ Conversas com IA (snoozed): {convs.count()}")
    
    for conv in convs[:3]:
        print(f"\n📱 Conversa ID: {conv.id}")
        print(f"   Status: {conv.status}")
        print(f"   Additional: {conv.additional_attributes}")
        print(f"   Contact: {conv.contact.name if conv.contact else 'N/A'}")
    
    # Verificar se há conversas com additional_attributes__has_key='ai_assisted'
    ai_assisted = Conversation.objects.filter(additional_attributes__has_key='ai_assisted')
    print(f"\n🔍 Conversas com 'ai_assisted': {ai_assisted.count()}")
    
    # Verificar todas as conversas ativas
    active_convs = Conversation.objects.exclude(status__in=['closed', 'resolved'])
    print(f"\n📊 Total de conversas ativas: {active_convs.count()}")
    
    status_counts = active_convs.values('status').annotate(count=models.Count('id'))
    for status in status_counts:
        print(f"   {status['status']}: {status['count']}")

if __name__ == "__main__":
    check_ai_conversations()
