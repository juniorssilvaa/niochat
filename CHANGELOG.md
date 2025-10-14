# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [2.4.0] - 2025-10-14

### Corrigido
- **Frontend**: Mapeamento de dados entre backend e frontend no Recuperador de Conversas
- **API**: Conversão correta de `provedorId` string para número na requisição
- **Dashboard**: Cards agora exibem dados corretos (tentativas, recuperadas, pendentes, taxa de conversão)
- **Termômetro**: Animação funciona corretamente com dados reais do backend
- **Mapeamento de Campos**: Backend `total_attempts` → Frontend `totalAttempts`
- **Mapeamento de Campos**: Backend `successful_recoveries` → Frontend `successfulRecoveries`
- **Mapeamento de Campos**: Backend `pending_recoveries` → Frontend `pendingRecoveries`
- **Mapeamento de Campos**: Backend `conversion_rate` → Frontend `conversionRate`

### Melhorado
- **Frontend**: Remoção de logs de debug desnecessários
- **Código**: Limpeza e organização do código do componente ConversationRecovery
- **Documentação**: Atualização completa da documentação MkDocs com endpoints de recuperação
- **README**: Seção detalhada sobre o Recuperador de Conversas com configurações e funcionalidades

## [2.3.0] - 2025-10-13

### Adicionado
- **🔄 Recuperador de Conversas**: Nova funcionalidade para recuperação automática de vendas
- **🤖 Análise Inteligente**: IA analisa conversas encerradas para identificar clientes interessados
- **📊 Dashboard Visual**: Termômetro animado de vendas recuperadas com porcentagem central
- **⚙️ Configurações Flexíveis**: Delay, tentativas máximas e critérios de análise personalizáveis
- **🔒 Isolamento por Provedor**: Cada provedor vê apenas seus dados de recuperação
- **📱 Mensagens Personalizadas**: IA gera mensagens de recuperação baseadas na análise da conversa
- **📈 Métricas Detalhadas**: Estatísticas de tentativas, recuperações e taxa de conversão
- **🎯 Processamento em Lote**: Análise e envio automático para múltiplos clientes
- **📋 API Completa**: Endpoints para estatísticas, análise, campanhas e configurações
- **🛠️ Comando Django**: `python manage.py run_recovery_analysis` para execução manual

### Melhorado
- **Frontend**: Interface responsiva com animações suaves no termômetro
- **Backend**: Sistema robusto de recuperação com verificações de segurança
- **Documentação**: README e API docs atualizados com nova funcionalidade

### Corrigido
- **Frontend**: Erro `TypeError: Cannot read properties of undefined` no dashboard
- **Verificações de Segurança**: Todos os acessos a objetos usam optional chaining (`?.`)
- **Renderização**: Verificações de existência antes de renderizar componentes

## [2.2.0] - 2025-10-11

### Adicionado
- Integração automática de fotos de perfil via Uazapi nos feedbacks CSAT
- Exibição da mensagem original do cliente nos "Últimos Feedbacks"
- Serialização completa dos dados CSAT usando `CSATFeedbackSerializer`
- Busca automática de avatars dos contatos via API Uazapi

### Corrigido
- **CSAT Dashboard**: Cards "Satisfação Média", "Total de Avaliações", "Taxa de Satisfação" agora exibem dados corretos do Supabase
- **Endpoint CSAT**: Erro 500 corrigido - problema de serialização com objetos `CSATFeedback`
- **Últimos Feedbacks**: Avatar e mensagem original agora são exibidos corretamente
- **Serialização JSON**: Corrigido erro `Object of type CSATFeedback is not JSON serializable`
- **Integração Uazapi**: Fotos de perfil agora são buscadas automaticamente
- **Dados CSAT**: Todos os dados agora são enviados para Supabase com isolamento por provedor

### Melhorado
- **Performance**: Uso de serializer otimizado para dados CSAT
- **Integração**: Melhor integração entre backend e frontend para dados CSAT
- **UX**: Dashboard CSAT com dados completos e fotos de perfil
- **Dados**: Isolamento total de dados por provedor via RLS no Supabase

## [2.1.0] - 2025-10-10

### Adicionado
- Sistema CSAT completo com coleta automática de feedback
- Dashboard CSAT com métricas em tempo real
- Integração com Supabase para dados de auditoria e CSAT
- IA interpreta feedback textual dinamicamente
- Envio automático de CSAT 1.5 minutos após fechamento

### Corrigido
- **Redis Memory**: Limpeza correta da memória após encerramento de conversas
- **Conversas**: Não reutiliza conversas fechadas incorretamente
- **IA**: Atualização automática do nome do contato quando descoberto via SGP
- **Dados**: Envio automático de conversas, contatos e mensagens para Supabase

### Melhorado
- **Arquitetura**: Separação clara entre dados locais e Supabase
- **Performance**: Otimização de consultas e serialização
- **Segurança**: Isolamento total de dados por provedor
- **UX**: Interface mais responsiva e intuitiva

## [2.0.0] - 2025-10-09

### Adicionado
- Sistema completo de atendimento WhatsApp
- Integração com IA OpenAI para respostas inteligentes
- Dashboard em tempo real com métricas avançadas
- Sistema multi-tenant com isolamento de dados
- Integração com SGP para consultas automáticas
- Sistema de auditoria completo
- Transcrição automática de áudio
- Suporte a mídia completa (imagens, vídeos, documentos)

### Melhorado
- **Performance**: Otimização de consultas e cache
- **Segurança**: Implementação de RLS no Supabase
- **UX**: Interface moderna e responsiva
- **Integração**: Melhor integração entre componentes

---

## Como Contribuir

Para contribuir com este projeto:

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.