# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.23.2] - 2025-09-29

### 🔧 Correções Finais e Otimizações
- **Sistema de Transferência Inteligente**: Corrigido problema onde a IA detectava necessidade de transferência mas não executava a transferência real. Sistema agora funciona 100%
- **Correção de Erros de Sintaxe**: Corrigidos erros de sintaxe em openai_service.py e views.py que causavam falhas no sistema
- **Correção de Variáveis Indefinidas**: Corrigidos erros de NameError para variáveis filename e file_size em mensagens de texto
- **Correção de Imports**: Movidos imports de tempfile e traceback para o topo dos arquivos para evitar erros de escopo
- **Otimização do Sistema de Detecção de Transferência**: Melhorada a lógica de detecção automática de transferências baseada na análise da conversa
- **Melhoria no Processamento de PDFs**: Corrigido fluxo de processamento de PDFs para evitar chamadas duplas da IA
- **Melhoria no Processamento de Imagens**: Corrigido download e análise de imagens com autenticação correta da API Uazapi

## [2.23.1] - 2025-09-29

### 🔧 Correções de Estabilidade
- **Correção no Sistema de Áudio**: Correção de bugs críticos no módulo de áudio que causavam instabilidade
- **Melhoria nas Transferências**: Otimização no sistema de transferências realizadas pela IA

## [2.23.0] - 2025-09-27

### 🚀 Nova IA Multimídia e Sistema CSAT
- **IA com Processamento de Áudio e Imagens**: Nova capacidade da IA para processar e entender arquivos de áudio e imagens
- **Sistema CSAT de Feedback**: Implementação de pesquisa de satisfação do cliente para coletar feedback dos clientes
- **Biblioteca de Sons Expandida**: Adicionados novos efeitos sonoros ao sistema
- **Auditoria com Fotos**: Agora é possível visualizar a foto do contato diretamente na aba de auditoria
- **Otimização de Transferências por IA**: Melhoria no sistema de transferências realizadas pela IA para maior eficiência
- **Correções no Sistema de Notificações**: Refatoração e correções no sistema de notificações

## [2.22.2] - 2025-09-27

### 🔧 Correções
- **Sistema de Atendimento**: Corrigida lógica de transferência de atendimentos
- **Sistema de Áudio**: Melhorado tratamento de erros no CustomAudioPlayer
- **IA e Processamento**: Corrigido prompt da IA para LED vermelho
- **Interface**: Removidos ícones desnecessários do chat interno

## [2.22.1] - 2025-09-26

### 🚀 Novas Funcionalidades
- **Implementado**: Atualização automática do changelog via sistema de versionamento

### 🔧 Correções
- **Corrigido**: Sistema de som, auditoria e exibição de versão no frontend

## [2.21.0] - 2025-09-26

### 🚀 Novas Funcionalidades
- **Implementado**: Sistema de atualização de mensagens em tempo real no chat interno

### 🔧 Correções
- **Corrigido**: Problema de exibição de mensagens do chat interno