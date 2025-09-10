#!/bin/bash

# Script para deploy automático no Portainer
# Configuração para produção com app.niochat.com.br

set -e

echo "🚀 Iniciando deploy para produção..."

# Configurações
PORTAINER_URL="https://portainer.niochat.com.br"
PORTAINER_USERNAME="admin"
PORTAINER_PASSWORD="Semfim01@"
STACK_NAME="niochat"
STACK_FILE="docker-compose-production.yml"

# Verificar se o arquivo existe
if [ ! -f "$STACK_FILE" ]; then
    echo "❌ Arquivo $STACK_FILE não encontrado!"
    exit 1
fi

echo "📋 Usando arquivo: $STACK_FILE"

# Fazer login no Portainer
echo "🔐 Fazendo login no Portainer..."
LOGIN_RESPONSE=$(curl -s -X POST "$PORTAINER_URL/api/auth" \
    -H "Content-Type: application/json" \
    -d "{\"Username\":\"$PORTAINER_USERNAME\",\"Password\":\"$PORTAINER_PASSWORD\"}")

# Extrair token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.jwt')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Falha no login no Portainer"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login realizado com sucesso"

# Obter ID do endpoint (Docker Swarm)
echo "🔍 Buscando endpoint..."
ENDPOINTS_RESPONSE=$(curl -s -X GET "$PORTAINER_URL/api/endpoints" \
    -H "Authorization: Bearer $TOKEN")

ENDPOINT_ID=$(echo "$ENDPOINTS_RESPONSE" | jq -r '.[0].Id')

if [ "$ENDPOINT_ID" = "null" ] || [ -z "$ENDPOINT_ID" ]; then
    echo "❌ Endpoint não encontrado"
    exit 1
fi

echo "✅ Endpoint encontrado: $ENDPOINT_ID"

# Verificar se a stack existe
echo "🔍 Verificando se a stack existe..."
STACKS_RESPONSE=$(curl -s -X GET "$PORTAINER_URL/api/stacks" \
    -H "Authorization: Bearer $TOKEN")

STACK_ID=$(echo "$STACKS_RESPONSE" | jq -r ".[] | select(.Name == \"$STACK_NAME\") | .Id")

if [ -n "$STACK_ID" ] && [ "$STACK_ID" != "null" ]; then
    echo "📝 Stack encontrada (ID: $STACK_ID). Atualizando..."
    
    # Atualizar stack existente
    STACK_CONTENT=$(cat "$STACK_FILE" | base64 -w 0)
    
    UPDATE_RESPONSE=$(curl -s -X PUT "$PORTAINER_URL/api/stacks/$STACK_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"StackFileContent\": \"$STACK_CONTENT\",
            \"Prune\": true
        }")
    
    echo "✅ Stack atualizada com sucesso!"
    
else
    echo "🆕 Stack não encontrada. Criando nova stack..."
    
    # Criar nova stack
    STACK_CONTENT=$(cat "$STACK_FILE" | base64 -w 0)
    
    CREATE_RESPONSE=$(curl -s -X POST "$PORTAINER_URL/api/stacks" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"Name\": \"$STACK_NAME\",
            \"StackFileContent\": \"$STACK_CONTENT\",
            \"SwarmID\": \"$ENDPOINT_ID\"
        }")
    
    NEW_STACK_ID=$(echo "$CREATE_RESPONSE" | jq -r '.Id')
    
    if [ "$NEW_STACK_ID" = "null" ] || [ -z "$NEW_STACK_ID" ]; then
        echo "❌ Falha ao criar stack"
        echo "Resposta: $CREATE_RESPONSE"
        exit 1
    fi
    
    echo "✅ Stack criada com sucesso! (ID: $NEW_STACK_ID)"
fi

echo "🎉 Deploy concluído com sucesso!"
echo "🌐 Acesse: https://app.niochat.com.br"
echo "👤 Login: Junior / Semfim01@"
