# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.8.2] - 2025-09-11

### 🔧 Correções Críticas

#### Deploy e Infraestrutura
- **Corrigido**: Lógica de remoção de imagens antigas no GitHub Actions
  - Agora remove corretamente imagens sem tag `:latest`
  - Mantém apenas a imagem mais recente (com tag `:latest`)
  - Evita acúmulo de imagens antigas no Portainer

- **Corrigido**: Health check do deploy
  - Aceita status 401 como saudável para `/api/auth/me/` (sem token)
  - Usa verificação de status HTTP em vez de `curl -f`
  - Melhora logs de health check com códigos de status
  - Corrige falha no deploy causada por health check incorreto

- **Corrigido**: Roteamento de webhooks no Traefik
  - Adicionada regra específica para `/webhook/` e `/webhooks/`
  - Prioridade 200 para garantir roteamento correto ao backend
  - Suporte a múltiplas rotas de webhook (com e sem barra final)
  - Corrige problema de webhooks retornando HTML do frontend

#### Frontend e WebSocket
- **Corrigido**: URLs de WebSocket para produção
  - Mudança de `ws://hostname:8010` para `wss://hostname`
  - Uso de porta padrão HTTPS (443) em vez de 8010
  - Correção em todos os componentes: `NotificationContext`, `PrivateChat`, `UserStatusManager`, `useOnlineUsers`, `ConversasDashboard`

- **Corrigido**: Problema de tela branca após login
  - Inicialização correta de `userRole` como `null` em `App.jsx`
  - Adicionado delay na conexão de WebSocket (1-2 segundos)
  - Verificação de `user.token` antes de conectar WebSocket
  - Previne conexões prematuras que causavam erros

- **Melhorado**: Logs de console
  - Removidos emojis de todos os logs de console
  - Removida exposição de tokens e informações sensíveis
  - Logs mais limpos e profissionais para produção

#### Sistema de Notificações
- **Corrigido**: Sistema de notificações de chat interno
  - Integração com WebSocket para notificações em tempo real
  - Contagem de mensagens não lidas funcionando corretamente
  - Auto-disappearing de notificações implementado
  - Cache agressivo para evitar mensagens "fixas"

### 🚀 Melhorias

#### GitHub Actions
- **Adicionado**: Job de validação do Portainer
  - Testa conexão com API do Portainer antes do deploy
  - Evita falhas de deploy por problemas de conectividade
  - Validação prévia de credenciais

- **Melhorado**: Processo de deploy automatizado
  - Remoção automática de imagens antigas
  - Pull forçado de novas imagens `:latest`
  - Atualização automática do stack no Portainer
  - Verificação de saúde após deploy

#### Segurança
- **Melhorado**: Middleware de autenticação WebSocket
  - Extração melhorada de tokens para WebSocket
  - Validação mais robusta de credenciais
  - Suporte a múltiplos formatos de token

### 🔗 Integrações

#### Webhooks Externos
- **Corrigido**: Roteamento de webhooks UazAPI/Evolution
  - Suporte a múltiplas rotas: `/webhook/`, `/webhooks/`
  - Roteamento correto via Traefik para backend
  - Processamento adequado de mensagens externas
  - Identificação automática de provedores por instância

### 📋 Detalhes Técnicos

#### Arquivos Modificados
- `.github/workflows/deploy.yml` - Correções no deploy e health check
- `docker-compose-fixed.yml` - Regras de roteamento Traefik
- `frontend/src/App.jsx` - Inicialização de userRole
- `frontend/src/contexts/NotificationContext.jsx` - URLs WebSocket
- `frontend/src/components/PrivateChat.jsx` - URLs WebSocket
- `frontend/src/components/UserStatusManager.jsx` - URLs WebSocket e logs
- `frontend/src/hooks/useOnlineUsers.js` - URLs WebSocket e logs
- `frontend/src/components/ConversasDashboard.jsx` - URLs WebSocket

#### URLs de Webhook Configuradas
- `https://app.niochat.com.br/webhook/evolution-uazapi/`
- `https://app.niochat.com.br/webhook/evolution-uazapi`
- `https://app.niochat.com.br/webhooks/evolution-uazapi/`
- `https://app.niochat.com.br/webhooks/evolution-uazapi`

### ✅ Status de Produção
- **Deploy**: ✅ Funcionando automaticamente via GitHub Actions
- **Health Check**: ✅ Corrigido e validando corretamente
- **Webhooks**: ✅ Roteamento corrigido e pronto para uso
- **WebSocket**: ✅ URLs corrigidas para produção
- **Notificações**: ✅ Sistema funcionando em tempo real
- **Remoção de Imagens**: ✅ Automática e eficiente

---

## [2.8.1] - 2025-09-10

### 🎉 Lançamento Inicial
- Sistema de chat interno implementado
- Integração com UazAPI e Evolution
- Deploy automatizado via GitHub Actions
- Interface de usuário moderna e responsiva
