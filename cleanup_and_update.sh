#!/bin/bash

echo "🔍 Limpando imagens antigas do NioChat..."

# Parar e remover containers em execução
echo "🛑 Parando containers do NioChat..."
docker stop niochat-frontend niochat-backend niochat-celery 2>/dev/null || true
docker rm niochat-frontend niochat-backend niochat-celery 2>/dev/null || true

# Remover imagens antigas (sem tag)
echo "🗑️ Removendo imagens antigas..."
docker images | grep "niochat" | grep "<none>" | awk '{print $3}' | xargs -r docker rmi 2>/dev/null || true

# Remover todas as imagens não utilizadas
echo "🧹 Limpando imagens não utilizadas..."
docker image prune -f

# Puxar as últimas imagens
echo "📥 Baixando as últimas imagens..."
docker pull ghcr.io/juniorssilvaa/niochat-frontend:latest
docker pull ghcr.io/juniorssilvaa/niochat-backend:latest

# Iniciar os serviços
echo "🚀 Iniciando serviços..."
docker-compose up -d

echo "✅ Processo concluído! As imagens foram atualizadas para as versões mais recentes."