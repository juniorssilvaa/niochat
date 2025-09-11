#!/bin/bash

echo "🛑 Parando ambiente de desenvolvimento com Traefik..."
echo ""

# Parar containers
echo "⏹️ Parando containers..."
docker-compose -f docker-compose.dev.yml down

# Remover containers órfãos
echo "🧹 Removendo containers órfãos..."
docker-compose -f docker-compose.dev.yml down --remove-orphans

echo "✅ Ambiente de desenvolvimento parado!"
echo ""
echo "💡 Para iniciar novamente: ./start-dev-traefik.sh"

