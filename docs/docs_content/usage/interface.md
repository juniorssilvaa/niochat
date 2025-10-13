# Interface do Usuário

Este guia explica como usar a interface do NioChat para gerenciar conversas, visualizar métricas e administrar o sistema.

## Acesso ao Sistema

### 1. Login
1. Acesse a URL do sistema: `http://localhost:5173`
2. Digite seu usuário e senha
3. Clique em "Entrar"

### 2. Primeiro Acesso
- **Usuário**: admin
- **Senha**: A senha definida durante a instalação
- **Alterar Senha**: Recomendado no primeiro acesso

## Dashboard Principal

### 1. Visão Geral
O dashboard principal exibe:
- **Total de Conversas**: Número total de conversas
- **Conversas Abertas**: Conversas em andamento
- **Taxa de Resolução**: Percentual de conversas resolvidas
- **Satisfação Média**: Média das avaliações CSAT
- **Tempo de Resposta**: Tempo médio de resposta

### 2. Gráficos Interativos
- **Evolução Temporal**: Gráfico de linha mostrando conversas ao longo do tempo
- **Distribuição por Status**: Gráfico de pizza com status das conversas
- **Performance por Agente**: Gráfico de barras com métricas individuais
- **Tendências CSAT**: Evolução da satisfação do cliente

### 3. Filtros
- **Por Data**: Selecione período específico
- **Por Agente**: Filtre por agente responsável
- **Por Equipe**: Filtre por equipe
- **Por Status**: Apenas conversas abertas, fechadas, etc.

## Gerenciamento de Conversas

### 1. Lista de Conversas
A lista de conversas mostra:
- **Cliente**: Nome e foto do contato
- **Última Mensagem**: Preview da última mensagem
- **Status**: Aberta, fechada, pendente
- **Agente**: Quem está atendendo
- **Tempo**: Há quanto tempo a conversa está ativa
- **Prioridade**: Indicador visual de urgência

### 2. Ações Disponíveis
- **Abrir Conversa**: Clique para abrir o chat
- **Atribuir**: Transferir para outro agente
- **Fechar**: Encerrar conversa
- **Marcar como Pendente**: Pausar atendimento
- **Transferir para Equipe**: Enviar para equipe específica

### 3. Busca e Filtros
- **Busca por Texto**: Digite para buscar em mensagens
- **Filtro por Status**: Dropdown com opções
- **Filtro por Agente**: Selecione agente específico
- **Ordenação**: Por data, prioridade, status

## Chat Interface

### 1. Área de Mensagens
- **Histórico**: Todas as mensagens da conversa
- **Tipos de Mídia**: Imagens, vídeos, áudios, documentos
- **Reações**: Emojis e reações personalizadas
- **Status de Entrega**: Confirmação de recebimento
- **Timestamp**: Hora de cada mensagem

### 2. Envio de Mensagens
- **Texto**: Digite e pressione Enter
- **Mídia**: Clique no ícone de anexo
- **Respostas Rápidas**: Templates pré-definidos
- **Emojis**: Seletor de emojis
- **Formatação**: Negrito, itálico, código

### 3. Funcionalidades Avançadas
- **IA Assistente**: Sugestões automáticas
- **Consulta SGP**: Botão para consultar dados do cliente
- **Histórico**: Ver conversas anteriores do cliente
- **Notas**: Adicionar notas internas
- **Tags**: Marcar conversa com tags

## Sistema CSAT

### 1. Configuração
- **Tempo de Envio**: 1.5 minutos após fechamento
- **Mensagem Personalizada**: Texto customizado por provedor
- **Canais**: WhatsApp, SMS, Email
- **Agendamento**: Horários específicos

### 2. Dashboard CSAT
- **Métricas Visuais**: Gráficos de satisfação
- **Distribuição de Ratings**: 1 a 5 estrelas
- **Evolução Temporal**: Tendências ao longo do tempo
- **Comparação**: Períodos diferentes

### 3. Últimos Feedbacks
- **Avatar do Cliente**: Foto de perfil
- **Rating Visual**: Emoji correspondente
- **Mensagem Original**: Feedback textual do cliente
- **Data/Hora**: Quando foi enviado
- **Análise IA**: Interpretação automática

## Administração

### 1. Usuários
- **Listar Usuários**: Todos os usuários do sistema
- **Criar Usuário**: Adicionar novo usuário
- **Editar Perfil**: Modificar dados do usuário
- **Permissões**: Definir níveis de acesso
- **Equipes**: Organizar usuários em equipes

### 2. Provedores
- **Configurações**: Dados do provedor
- **Integrações**: WhatsApp, SGP, Supabase
- **Limites**: Controles de uso
- **Billing**: Informações de cobrança

### 3. Configurações
- **Sistema**: Configurações gerais
- **IA**: Parâmetros da inteligência artificial
- **Notificações**: Alertas e lembretes
- **Backup**: Configurações de backup
- **Logs**: Visualização de logs

## Chat Interno

### 1. Salas de Chat
- **Criar Sala**: Nova sala para equipe
- **Participantes**: Adicionar/remover membros
- **Histórico**: Mensagens salvas
- **Notificações**: Alertas de mensagens

### 2. Chat Privado
- **Mensagens Diretas**: Entre usuários
- **Status Online**: Quem está conectado
- **Notificações**: Alertas de mensagens
- **Histórico**: Mensagens salvas

## Auditoria

### 1. Logs de Auditoria
- **Ações**: Todas as ações do sistema
- **Usuários**: Quem fez o quê
- **Timestamps**: Quando aconteceu
- **Detalhes**: Informações completas

### 2. Filtros de Auditoria
- **Por Ação**: Tipo de ação
- **Por Usuário**: Ações de usuário específico
- **Por Data**: Período específico
- **Por Provedor**: Isolamento de dados

### 3. Exportação
- **PDF**: Relatórios em PDF
- **Excel**: Dados em planilha
- **CSV**: Dados estruturados
- **JSON**: Dados brutos

## Atalhos de Teclado

### 1. Navegação
- **Ctrl + K**: Busca global
- **Ctrl + N**: Nova conversa
- **Ctrl + F**: Busca na conversa
- **Esc**: Fechar modais

### 2. Chat
- **Enter**: Enviar mensagem
- **Shift + Enter**: Nova linha
- **Ctrl + A**: Selecionar tudo
- **Ctrl + Z**: Desfazer

### 3. Sistema
- **Ctrl + S**: Salvar
- **Ctrl + R**: Atualizar
- **F5**: Recarregar página
- **Ctrl + Shift + R**: Recarregar forçado

## Notificações

### 1. Tipos de Notificação
- **Nova Mensagem**: Cliente enviou mensagem
- **Conversa Atribuída**: Nova conversa para você
- **CSAT Recebido**: Feedback de satisfação
- **Sistema**: Alertas do sistema

### 2. Configurações
- **Som**: Ativar/desativar sons
- **Desktop**: Notificações do sistema
- **Email**: Notificações por email
- **Push**: Notificações push

### 3. Gerenciamento
- **Marcar como Lida**: Marcar notificação
- **Arquivar**: Remover da lista
- **Configurar**: Personalizar alertas
- **Histórico**: Ver notificações antigas

## Troubleshooting

### 1. Problemas Comuns
- **Página não carrega**: Verificar conexão
- **Mensagens não aparecem**: Recarregar página
- **Erro de permissão**: Verificar usuário
- **Lentidão**: Verificar conexão

### 2. Soluções
- **Recarregar**: F5 ou Ctrl + R
- **Limpar Cache**: Ctrl + Shift + R
- **Logout/Login**: Sair e entrar novamente
- **Suporte**: Contatar administrador

### 3. Logs
- **Console**: F12 para ver erros
- **Network**: Verificar requisições
- **Application**: Verificar storage
- **Security**: Verificar certificados

## Próximos Passos

1. [API](api/endpoints.md) - Explore a API
2. [Troubleshooting](development/troubleshooting.md) - Resolva problemas
3. [Configuração](configuration/supabase.md) - Configure integrações