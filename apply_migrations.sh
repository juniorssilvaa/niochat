#!/bin/bash

# Script para aplicar migrações do Django no ambiente de produção
# Este script deve ser executado dentro do container do backend

echo "🔄 Iniciando processo de aplicação de migrações..."

# Verificar se estamos no ambiente de produção
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py não encontrado. Este script deve ser executado no diretório do projeto Django."
    exit 1
fi

# Aplicar migrações
echo "📋 Aplicando migrações pendentes..."
python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo "✅ Migrações aplicadas com sucesso!"
else
    echo "❌ Erro ao aplicar migrações."
    exit 1
fi

# Coletar arquivos estáticos
echo "📂 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    echo "✅ Arquivos estáticos coletados com sucesso!"
else
    echo "❌ Erro ao coletar arquivos estáticos."
    exit 1
fi

echo "🎉 Processo de atualização concluído com sucesso!"