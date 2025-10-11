#!/usr/bin/env python
"""
Script para sincronizar dados existentes com o Supabase
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/home/junior/niochat/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from conversations.models import Conversation, Contact, Message, CSATFeedback
from core.supabase_service import supabase_service
from django.utils import timezone

def sync_conversation_to_supabase(conversation_id):
    """Sincronizar uma conversa específica com o Supabase"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        contact = conversation.contact
        provedor = conversation.inbox.provedor
        
        print(f"🔄 Sincronizando conversa {conversation_id}...")
        
        # 1. Enviar contato para Supabase
        contact_success = supabase_service.save_contact(
            provedor_id=provedor.id,
            contact_id=contact.id,
            name=contact.name,
            phone=contact.phone,
            email=contact.email,
            avatar=contact.avatar,
            created_at_iso=contact.created_at.isoformat(),
            updated_at_iso=contact.updated_at.isoformat(),
            additional_attributes=contact.additional_attributes
        )
        
        if contact_success:
            print(f"  ✅ Contato {contact.name} enviado para Supabase")
        else:
            print(f"  ❌ Falha ao enviar contato {contact.name}")
        
        # 2. Enviar conversa para Supabase
        conversation_success = supabase_service.save_conversation(
            provedor_id=provedor.id,
            conversation_id=conversation.id,
            contact_id=contact.id,
            inbox_id=conversation.inbox.id if conversation.inbox else None,
            status=conversation.status,
            assignee_id=conversation.assignee.id if conversation.assignee else None,
            created_at_iso=conversation.created_at.isoformat(),
            updated_at_iso=conversation.updated_at.isoformat(),
            ended_at_iso=conversation.ended_at.isoformat() if hasattr(conversation, 'ended_at') and conversation.ended_at else None,
            additional_attributes=conversation.additional_attributes
        )
        
        if conversation_success:
            print(f"  ✅ Conversa {conversation.id} enviada para Supabase")
        else:
            print(f"  ❌ Falha ao enviar conversa {conversation.id}")
        
        # 3. Enviar mensagens para Supabase
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        print(f"  📤 Enviando {messages.count()} mensagens...")
        
        messages_success = 0
        for msg in messages:
            success = supabase_service.save_message(
                provedor_id=provedor.id,
                conversation_id=conversation.id,
                contact_id=contact.id,
                content=msg.content,
                message_type=msg.message_type,
                is_from_customer=msg.is_from_customer,
                external_id=msg.external_id,
                file_url=msg.file_url,
                file_name=msg.file_name,
                file_size=msg.file_size,
                additional_attributes=msg.additional_attributes,
                created_at_iso=msg.created_at.isoformat()
            )
            
            if success:
                messages_success += 1
        
        print(f"  ✅ {messages_success}/{messages.count()} mensagens enviadas")
        
        # 4. Verificar CSAT
        csat_feedback = CSATFeedback.objects.filter(conversation=conversation).first()
        if csat_feedback:
            print(f"  📊 CSAT já existe: {csat_feedback.emoji_rating} (rating: {csat_feedback.rating_value})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao sincronizar conversa {conversation_id}: {e}")
        return False

if __name__ == "__main__":
    # Sincronizar conversa 49
    sync_conversation_to_supabase(49)
