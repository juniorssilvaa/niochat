#!/bin/bash

# Script para deploy automático da documentação
# Este script deve ser executado no servidor após o build do GitHub Actions

echo "🚀 Iniciando deploy da documentação NioChat..."

# 1. Verificar se o volume existe
echo "📁 Verificando volume Docker..."
if ! sudo docker volume ls | grep -q niochat-docs; then
    echo "📦 Criando volume niochat-docs..."
    sudo docker volume create niochat-docs
fi

# 2. Verificar se a documentação foi gerada
if [ ! -d "/home/junior/niochat/docs/site" ]; then
    echo "❌ Documentação não encontrada! Executando build..."
    cd /home/junior/niochat/docs
    
    # Ativar ambiente virtual se existir
    if [ -d "mkdocs_env" ]; then
        source mkdocs_env/bin/activate
    fi
    
    # Instalar dependências se necessário
    pip install mkdocs mkdocs-material
    
    # Gerar documentação
    mkdocs build
fi

# 3. Copiar arquivos para o volume
echo "📋 Copiando arquivos para o volume Docker..."
sudo rm -rf /var/lib/docker/volumes/niochat-docs/_data/*
sudo cp -r /home/junior/niochat/docs/site/* /var/lib/docker/volumes/niochat-docs/_data/

# 4. Verificar se o container está rodando
echo "🐳 Verificando container de documentação..."
if ! sudo docker ps | grep -q niochat-docs; then
    echo "🔄 Iniciando container de documentação..."
    cd /home/junior/niochat
    sudo docker-compose up -d niochat-docs
else
    echo "🔄 Reiniciando container de documentação..."
    sudo docker restart niochat-docs
fi

# 5. Verificar se está funcionando
echo "✅ Verificando se a documentação está funcionando..."
sleep 5
if curl -f -s "https://docs.niochat.com.br" > /dev/null; then
    echo "🎉 Documentação deployada com sucesso!"
    echo "🌐 Acesse: https://docs.niochat.com.br"
else
    echo "⚠️ Documentação pode estar ainda inicializando..."
    echo "🌐 Acesse: https://docs.niochat.com.br"
fi
