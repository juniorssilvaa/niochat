#!/bin/bash

echo "🚀 Iniciando ambiente de desenvolvimento com Traefik..."
echo ""

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f docker-compose.dev.yml down

# Remover containers órfãos
echo "🧹 Removendo containers órfãos..."
docker-compose -f docker-compose.dev.yml down --remove-orphans

# Construir e iniciar containers
echo "🔨 Construindo e iniciando containers..."
docker-compose -f docker-compose.dev.yml up --build -d

# Aguardar containers iniciarem
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Verificar status
echo "📊 Status dos containers:"
docker-compose -f docker-compose.dev.yml ps

echo ""
echo "✅ Ambiente de desenvolvimento iniciado!"
echo ""
echo "🌐 URLs disponíveis:"
echo "  - Frontend: http://localhost"
echo "  - API: http://localhost/api/"
echo "  - Admin: http://localhost/admin/"
echo "  - Traefik Dashboard: http://localhost:8080"
echo ""
echo "🔧 Comandos úteis:"
echo "  - Ver logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Parar: docker-compose -f docker-compose.dev.yml down"
echo "  - Reiniciar: docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "📝 Para criar superusuário:"
echo "  docker exec -it niochat-backend-dev python manage.py createsuperuser"

