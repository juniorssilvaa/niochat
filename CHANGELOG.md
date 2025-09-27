# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.22.1] - 2025-09-26

### 🚀 Novas Funcionalidades
- **Implementado**: Atualização automática do changelog via sistema de versionamento
  - Versão do sistema agora sincronizada corretamente com o changelog
  - Sistema de versionamento automático integrado com o CHANGELOG.json
  - Endpoint `/api/changelog/` agora retorna versão atual do sistema

### 🔧 Correções
- **Corrigido**: Sistema de som
  - Corrigido problemas no sistema de notificações sonoras
  - Melhorias na reprodução e configuração de sons do sistema
- **Corrigido**: Sistema de auditoria
  - Corrigido problemas no sistema de auditoria de conversas
  - Melhorias na exibição e registro de atividades auditadas
- **Corrigido**: Exibição de versão no frontend
  - Versão atual do sistema agora é exibida dinamicamente no changelog
  - Endpoint `/api/changelog/` agora usa a versão do settings em vez de versão fixa
- **Melhorado**: Sistema de versionamento automático
  - Arquivo CHANGELOG.json mantém sincronizado com o sistema
  - Cópia automática para frontend/public/CHANGELOG.json

## [2.21.0] - 2025-09-26

### 🚀 Novas Funcionalidades
- **Implementado**: Sistema de atualização de mensagens em tempo real no chat interno
  - Mensagens agora aparecem em tempo real sem necessidade de recarregar
  - Implementado "optimistic update" para melhor experiência do usuário
  - Correção de duplicação de mensagens temporárias
- **Melhorado**: Gestão de mensagens temporárias no frontend
  - Implementado tratamento seguro de mensagens temporárias
  - Evita duplicatas ao receber confirmação via WebSocket

### 🔧 Correções
- **Corrigido**: Problema de exibição de mensagens do chat interno
  - Mensagens agora aparecem imediatamente após envio
  - WebSocket agora funciona corretamente para atualização em tempo real
  - Melhoria na decodificação segura de tokens JWT
- **Melhorado**: Tratamento de erros e segurança
  - Implementado tratamento seguro de decodificação de JWT
  - Melhorias na validação de mensagens temporárias

## [2.20.13] - 2025-09-23

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.12] - 2025-09-23

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.11] - 2025-09-21

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.10] - 2025-09-21

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.9] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.8] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.7] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.6] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.5] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.4] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.3] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.2] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.1] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.20.0] - 2025-09-17

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.19.3] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.19.2] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.19.1] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.19.0] - 2025-09-17

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.18.3] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.18.2] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.18.1] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.18.0] - 2025-09-17

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.17.4] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.17.3] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.17.2] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.17.1] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.17.0] - 2025-09-17

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.16.1] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.16.0] - 2025-09-17

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.15.15] - 2025-09-17

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.14] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.13] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.12] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.11] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.10] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.9] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.8] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.7] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.6] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.5] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.4] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.3] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.2] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.1] - 2025-09-16

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.15.0] - 2025-09-15

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.14.5] - 2025-09-15

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.14.4] - 2025-09-15

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.14.3] - 2025-09-15

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.14.2] - 2025-09-15

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.14.1] - 2025-09-15

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.14.0] - 2025-09-15

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.13.0] - 2025-09-15

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.12.0] - 2025-09-15

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.11.0] - 2025-09-15

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.10.5] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.10.4] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.10.3] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.10.2] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.10.1] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.10.0] - 2025-09-12

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.9.6] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.5] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.4] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.3] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.2] - 2025-09-12

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.1] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.9.0] - 2025-09-11

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.8.13] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.12] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.11] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.10] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.9] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.8] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.7] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.6] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.5] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.4] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.3] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.2] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.1] - 2025-09-11

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.8.0] - 2025-09-10

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.7.9] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.8] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.7] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.6] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.5] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.4] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.3] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.2] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.1] - 2025-09-10

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.7.0] - 2025-09-09

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.6.1] - 2025-09-09

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.6.0] - 2025-09-09

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.5.12] - 2025-09-09

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.11] - 2025-09-09

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.10] - 2025-09-09

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.9] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.8] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.7] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.6] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.5] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.4] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.3] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.2] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.1] - 2025-09-08

### 🔧 Correções e Melhorias
- **Atualizado**: Manutenção de sistema e melhorias de estabilidade

## [2.5.0] - 2025-09-08

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.4.0] - 2025-09-08

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.3.0] - 2025-09-08

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade

## [2.2.0] - 2025-09-08

### 🚀 Novas Funcionalidades
- **Adicionado**: Novas funcionalidades de sistema mantendo compatibilidade
