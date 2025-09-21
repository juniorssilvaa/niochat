#!/usr/bin/env python
"""
Script para criar/atualizar o superusuário Junior
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_or_update_superuser():
    User = get_user_model()
    
    username = "Junior"
    email = "admin@niochat.com.br"
    password = "Semfim01@"
    
    try:
        # Buscar ou criar usuário
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        # Atualizar senha e permissões
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.email = email
        user.save()
        
        if created:
            print(f"✅ Superusuário '{username}' criado com sucesso!")
        else:
            print(f"✅ Superusuário '{username}' atualizado com sucesso!")
            
        print(f"   Usuário: {username}")
        print(f"   Email: {email}")
        print(f"   Senha: {password}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_active: {user.is_active}")
        
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar superusuário: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_or_update_superuser()
