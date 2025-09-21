#!/bin/bash

# Script para atualizar a stack do Celery manualmente
echo "🔄 Atualizando stack do Celery..."

# Configurações
PORTAINER_URL="https://portainer.niochat.com.br"
PORTAINER_API_KEY="your_api_key_here"  # Substitua pela sua API key
STACK_NAME="niochat"

# Pegar ID da stack
echo "📋 Buscando ID da stack..."
STACK_ID=$(curl -s -H "X-API-Key: $PORTAINER_API_KEY" \
  "$PORTAINER_URL/api/stacks" | jq -r '.[] | select(.Name == "'$STACK_NAME'") | .Id')

if [ -z "$STACK_ID" ] || [ "$STACK_ID" = "null" ]; then
  echo "❌ Stack '$STACK_NAME' não encontrada!"
  exit 1
fi

echo "✅ Stack encontrada: $STACK_NAME (ID: $STACK_ID)"

# Ler o docker-compose.yml atual
echo "📖 Lendo docker-compose.yml..."
COMPOSE_CONTENT=$(cat docker-compose.yml)

# Escapar aspas e quebras de linha para JSON
COMPOSE_CONTENT_ESCAPED=$(echo "$COMPOSE_CONTENT" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Atualizar a stack
echo "🚀 Atualizando stack..."
RESPONSE=$(curl -s -X PUT \
  -H "X-API-Key: $PORTAINER_API_KEY" \
  -H "Content-Type: application/json" \
  --data "{
    \"Env\": [],
    \"StackFileContent\": \"$COMPOSE_CONTENT_ESCAPED\"
  }" \
  "$PORTAINER_URL/api/stacks/$STACK_ID?endpointId=1&pullImage=true&forceRecreate=true")

if echo "$RESPONSE" | grep -q "error"; then
  echo "❌ Erro ao atualizar stack:"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo "✅ Stack atualizada com sucesso!"
echo "⏳ Aguardando containers subirem..."
sleep 30

# Verificar status dos containers
echo "🔍 Verificando status dos containers..."
docker ps --filter "name=niochat" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

echo "🎉 Atualização concluída!"
