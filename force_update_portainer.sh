#!/bin/bash

# Script para forçar atualização das imagens no Portainer
# Este script remove imagens antigas e força o pull das latest

echo "🔄 Iniciando processo de atualização de imagens no Portainer..."

# Configurações
PORTAINER_URL="https://portainer.niochat.com.br"
PORTAINER_API_KEY="${PORTAINER_API_KEY:-$(cat /run/secrets/portainer_api_key 2>/dev/null || echo "")}"

if [ -z "$PORTAINER_API_KEY" ]; then
    echo "❌ PORTAINER_API_KEY não encontrada. Defina a variável de ambiente ou crie o secret."
    exit 1
fi

# Nome da stack
STACK_NAME="niochat"

echo "🔍 Procurando stack '$STACK_NAME'..."

# Pegar ID da stack
STACK_ID=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" \
  "$PORTAINER_URL/api/stacks" | jq -r ".[] | select(.Name == \"$STACK_NAME\") | .Id")

if [ -z "$STACK_ID" ] || [ "$STACK_ID" = "null" ]; then
  echo "❌ Stack '$STACK_NAME' não encontrada no Portainer."
  exit 1
fi

echo "✅ Stack encontrada: $STACK_NAME (ID: $STACK_ID)"

# Buscar stack file atual
echo "📥 Obtendo configuração atual da stack..."
CURRENT_STACK=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" \
  "$PORTAINER_URL/api/stacks/$STACK_ID/file")

if [ -z "$CURRENT_STACK" ]; then
  echo "❌ Erro ao buscar configuração da stack"
  exit 1
fi

# Atualizar imagens com latest - versão mais robusta
echo "🔧 Atualizando imagens para usar tag 'latest'..."
UPDATED_STACK=$(echo "$CURRENT_STACK" | jq '
  .StackFileContent = (.StackFileContent |
    gsub("ghcr\\.io/juniorssilvaa/niochat-backend:[^\\s]+"; "ghcr.io/juniorssilvaa/niochat-backend:latest") |
    gsub("ghcr\\.io/juniorssilvaa/niochat-frontend:[^\\s]+"; "ghcr.io/juniorssilvaa/niochat-frontend:latest")
  )
')

# Forçar Portainer a atualizar a stack
echo "🚀 Enviando atualização para o Portainer..."
RESPONSE=$(curl -s -X PUT \
  -H "X-API-Key: $PORTAINER_API_KEY" \
  -H "Content-Type: application/json" \
  --data "$UPDATED_STACK" \
  "$PORTAINER_URL/api/stacks/$STACK_ID?endpointId=1")

if [ -n "$RESPONSE" ] && echo "$RESPONSE" | grep -q "error"; then
  echo "❌ Erro na atualização da stack:"
  echo "$RESPONSE" | jq '.message'
  exit 1
fi

echo "✅ Stack atualizada com sucesso no Portainer!"

# Comandos adicionais para forçar atualização das imagens
echo "🔄 Forçando atualização das imagens no Docker..."

# Remover imagens antigas com tag <none>
echo "🗑️ Removendo imagens antigas (dangling)..."
docker image prune -f 2>/dev/null || true

# Pull das imagens latest
echo "📥 Baixando as últimas imagens..."
docker pull ghcr.io/juniorssilvaa/niochat-backend:latest 2>/dev/null || true
docker pull ghcr.io/juniorssilvaa/niochat-frontend:latest 2>/dev/null || true

# Reiniciar serviços
echo "🔄 Reiniciando serviços..."
docker service update --force niochat_backend 2>/dev/null || true
docker service update --force niochat_frontend 2>/dev/null || true

echo "✅ Processo de atualização concluído!"
echo "📊 Verificando status dos serviços..."
docker service ls | grep niochat || true

echo "💡 Se os serviços não forem encontrados, execute manualmente:"
echo "   docker stack deploy -c docker-compose.yml niochat"