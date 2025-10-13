#!/bin/bash

# Script para criar superadmin no sistema de produção
# Usuário: Junior
# Senha: Semfim01@

echo "🔐 Criando superadmin no sistema NioChat..."

# Navegar para o diretório backend
cd /home/junior/niochat/backend

# Ativar ambiente virtual se existir
if [ -d "../venv" ]; then
    echo "📦 Ativando ambiente virtual..."
    source ../venv/bin/activate
fi

# Executar comando Django para criar superadmin
echo "👤 Criando usuário superadmin..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

# Verificar se o usuário já existe
if User.objects.filter(username='Junior').exists():
    print("⚠️  Usuário 'Junior' já existe!")
    user = User.objects.get(username='Junior')
    user.set_password('Semfim01@')
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()
    print("✅ Usuário 'Junior' atualizado com sucesso!")
else:
    # Criar novo superadmin
    user = User.objects.create_superuser(
        username='Junior',
        email='junior@niochat.com.br',
        password='Semfim01@',
        first_name='Junior',
        last_name='Silva'
    )
    print("✅ Superadmin 'Junior' criado com sucesso!")

print(f"👤 Usuário: Junior")
print(f"🔑 Senha: Semfim01@")
print(f"🌐 Acesse: https://niochat.com.br/admin")
EOF

echo "🎉 Superadmin criado/atualizado com sucesso!"
