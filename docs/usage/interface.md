# Interface do Usuário

O NioChat oferece uma interface moderna e intuitiva para gerenciar atendimentos via WhatsApp. Esta seção explica como usar cada componente da interface.

## 🎯 Visão Geral

### Componentes Principais
- **Dashboard**: Métricas e relatórios em tempo real
- **Chat**: Interface de conversas
- **Auditoria**: Histórico completo de ações
- **Admin**: Painel de administração
- **Configurações**: Personalização do sistema

## 📊 Dashboard Principal

### Cards de Métricas
O dashboard exibe métricas em tempo real:

#### Taxa de Satisfação Média
- **Fonte**: Supabase (tabela `csat_feedback`)
- **Cálculo**: Média das avaliações (1-5)
- **Atualização**: Tempo real via WebSocket
- **Filtro**: Por provedor e período

#### Taxa de Resolução
- **Fonte**: Supabase (tabela `auditoria`)
- **Cálculo**: Conversas resolvidas / Total de conversas
- **Atualização**: Tempo real via WebSocket
- **Filtro**: Por provedor e período

### Gráficos Interativos
- **Evolução Temporal**: Métricas ao longo do tempo
- **Distribuição por Equipe**: Performance por equipe
- **Análise de Sentimento**: Feedback dos clientes
- **Tendências**: Padrões e tendências

## 💬 Interface de Chat

### Abas de Conversas
O sistema organiza conversas em abas inteligentes:

#### Com IA
- **Conversas com IA**: Atendimento automatizado
- **Status**: Aberta, fechada, pendente
- **Filtros**: Por equipe, agente, status
- **Ações**: Atribuir, transferir, fechar

#### Em Espera
- **Conversas Pendentes**: Aguardando atendimento
- **Transferências**: Conversas transferidas para equipes
- **Filtros**: Por equipe, prioridade
- **Ações**: Atribuir para agente específico

#### Em Atendimento
- **Conversas Ativas**: Em andamento
- **Atribuídas**: Para agentes específicos
- **Filtros**: Por agente, equipe
- **Ações**: Transferir, fechar, reabrir

### Funcionalidades do Chat
- **Mensagens em Tempo Real**: WebSocket
- **Envio de Mídia**: Imagens, vídeos, áudios
- **Reações**: Emojis em mensagens
- **Exclusão**: Deletar mensagens
- **Status**: Confirmação de entrega
- **Histórico**: Todas as mensagens

## 🔍 Sistema de Auditoria

### Logs de Auditoria
- **Ações do Sistema**: Login, logout, ações
- **Conversas**: Criação, fechamento, transferência
- **Mensagens**: Envio, recebimento, exclusão
- **CSAT**: Coleta e processamento de feedback

### Filtros Avançados
- **Por Data**: Período específico
- **Por Usuário**: Ações de usuário específico
- **Por Ação**: Tipo de ação
- **Por Provedor**: Dados do provedor

### Visualização
- **Lista Detalhada**: Todas as ações
- **Modal de Detalhes**: Informações completas
- **Exportação**: Dados em formato estruturado
- **Busca**: Pesquisa por texto

## 👥 Gestão de Equipes

### Criação de Equipes
1. Acesse **Admin > Equipes**
2. Clique em **Adicionar Equipe**
3. Preencha:
   - **Nome**: Nome da equipe
   - **Descrição**: Descrição da equipe
   - **Provedor**: Provedor da equipe
4. Clique em **Salvar**

### Adicionar Membros
1. Vá para a equipe criada
2. Clique em **Adicionar Membro**
3. Selecione o usuário
4. Defina as permissões
5. Clique em **Salvar**

### Transferência para Equipes
1. Abra uma conversa
2. Clique em **Transferir**
3. Selecione **Para Equipe**
4. Escolha a equipe
5. Confirme a transferência

## 🔧 Configurações

### Perfil do Usuário
- **Dados Pessoais**: Nome, email, telefone
- **Foto de Perfil**: Upload de imagem
- **Preferências**: Tema, idioma, notificações
- **Senha**: Alteração de senha

### Configurações do Sistema
- **Provedor**: Dados da empresa
- **Integrações**: WhatsApp, Telegram, Email
- **IA**: Configurações da IA
- **SGP**: Configurações do SGP
- **Supabase**: Configurações do Supabase

## 📱 Responsividade

### Desktop
- **Layout Completo**: Todas as funcionalidades
- **Sidebar**: Navegação lateral
- **Dashboard**: Métricas em tempo real
- **Chat**: Interface completa

### Mobile
- **Layout Adaptado**: Interface otimizada
- **Navegação**: Menu hambúrguer
- **Touch**: Gestos touch otimizados
- **Performance**: Carregamento rápido

### Tablet
- **Layout Híbrido**: Combinação de desktop e mobile
- **Navegação**: Adaptada ao tamanho
- **Funcionalidades**: Todas disponíveis
- **Otimização**: Para touch e mouse

## 🎨 Temas e Personalização

### Tema Claro
- **Cores**: Tons claros e suaves
- **Contraste**: Alto contraste para legibilidade
- **Ícones**: Estilo minimalista
- **Tipografia**: Fonte clara e legível

### Tema Escuro
- **Cores**: Tons escuros e elegantes
- **Contraste**: Contraste otimizado
- **Ícones**: Estilo moderno
- **Tipografia**: Fonte otimizada para escuro

### Personalização
- **Cores**: Cores personalizadas por provedor
- **Logo**: Logo da empresa
- **Favicon**: Ícone personalizado
- **Branding**: Identidade visual

## 🔔 Notificações

### Tipos de Notificação
- **Nova Mensagem**: Cliente enviou mensagem
- **Transferência**: Conversa transferida
- **CSAT**: Feedback recebido
- **Sistema**: Alertas do sistema

### Configurações
- **Som**: Notificações sonoras
- **Visual**: Notificações visuais
- **Email**: Notificações por email
- **Push**: Notificações push (futuro)

## 📊 Relatórios

### Relatórios Disponíveis
- **Performance**: Métricas de performance
- **Satisfação**: Análise de CSAT
- **Produtividade**: Análise de produtividade
- **Tendências**: Análise de tendências

### Exportação
- **PDF**: Relatórios em PDF
- **Excel**: Dados em Excel
- **CSV**: Dados em CSV
- **JSON**: Dados em JSON

## 🚀 Atalhos de Teclado

### Navegação
- **Ctrl + 1**: Dashboard
- **Ctrl + 2**: Chat
- **Ctrl + 3**: Auditoria
- **Ctrl + 4**: Admin

### Chat
- **Enter**: Enviar mensagem
- **Ctrl + Enter**: Nova linha
- **Esc**: Fechar modal
- **Ctrl + K**: Buscar conversa

### Ações
- **Ctrl + A**: Atribuir conversa
- **Ctrl + T**: Transferir conversa
- **Ctrl + F**: Fechar conversa
- **Ctrl + R**: Reabrir conversa

## 🐛 Troubleshooting

### Problemas Comuns

#### Interface não carrega
```bash
# Verifique se o frontend está rodando
curl http://localhost:5173

# Verifique os logs
tail -f logs/frontend.log
```

#### Chat não conecta
```bash
# Verifique o WebSocket
curl -I http://localhost:8010/ws/dashboard/

# Verifique o Redis
redis-cli ping
```

#### Dashboard não atualiza
```bash
# Verifique o Supabase
# Verifique as variáveis de ambiente
echo $VITE_SUPABASE_URL
echo $VITE_SUPABASE_KEY
```

#### Mensagens não aparecem
```bash
# Verifique o WebSocket
# Verifique os logs do backend
tail -f logs/backend.log
```

## 📚 Próximos Passos

1. [:octicons-arrow-right-24: Chat](usage/chat.md) - Aprenda a usar o chat
2. [:octicons-arrow-right-24: Dashboard](usage/dashboard.md) - Aprenda a usar o dashboard
3. [:octicons-arrow-right-24: Admin](usage/admin.md) - Aprenda a usar o admin
4. [:octicons-arrow-right-24: API](api/endpoints.md) - Aprenda a usar a API

