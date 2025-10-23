# Recuperador de Conversas

O Recuperador de Conversas é uma funcionalidade avançada que utiliza IA para identificar clientes interessados em planos de internet e reativá-los automaticamente através de mensagens personalizadas.

## 🎯 Funcionalidades

### Análise Inteligente
- **IA Avançada**: Analisa conversas encerradas para identificar interesse em planos
- **Critérios Personalizáveis**: Palavras-chave de interesse e barreiras configuráveis
- **Níveis de Interesse**: Classifica clientes em alto, médio ou baixo interesse
- **Análise de Barreiras**: Identifica obstáculos que impediram a venda

### Dashboard Visual
- **Termômetro Animado**: Visualização da taxa de conversão com animação gradual
- **Estatísticas em Tempo Real**: Tentativas, recuperações e pendências
- **Lista de Conversas**: Histórico detalhado das tentativas de recuperação
- **Métricas de Performance**: Taxa de conversão e tempo de resposta

### Configurações Flexíveis
- **Delay Personalizado**: Tempo de espera antes de enviar mensagem de recuperação
- **Tentativas Máximas**: Limite de tentativas por cliente
- **Horário de Funcionamento**: Configuração de horários para envio
- **Critérios de Análise**: Palavras-chave e filtros personalizáveis

## 🚀 Como Usar

### 1. Acessar o Dashboard
Navegue para **Recuperador de conversas** no menu lateral do sistema.

### 2. Visualizar Estatísticas
O dashboard mostra:
- **Termômetro**: Taxa de conversão visual com animação
- **Cards de Estatísticas**: Tentativas, recuperações, pendências
- **Lista de Conversas**: Histórico das tentativas de recuperação

### 3. Configurar Parâmetros
Ajuste as configurações:
- **Ativar Recuperador**: Liga/desliga o sistema
- **Máximo de Tentativas**: Número máximo de tentativas por cliente
- **Delay**: Tempo de espera em minutos
- **Análise Automática**: Ativar análise automática de conversas

### 4. Executar Análise
Use o comando Django para análise manual:
```bash
python manage.py run_recovery_analysis --days-back 7 --send-messages
```

## 📊 API Endpoints

### Estatísticas de Recuperação
```http
GET /api/recovery/stats/?provedor_id=1
```

### Analisar Conversas
```http
POST /api/recovery/analyze/
{
  "days_back": 7
}
```

### Enviar Campanha
```http
POST /api/recovery/campaign/
{
  "days_back": 7
}
```

### Configurações
```http
GET /api/recovery/settings/
PUT /api/recovery/settings/update/
```

## 🔧 Configuração Técnica

### Isolamento por Provedor
Cada provedor tem acesso apenas aos seus dados de recuperação, garantindo total isolamento.

### Integração com IA
O sistema utiliza OpenAI para:
- Análise de conversas
- Geração de mensagens personalizadas
- Identificação de barreiras de venda

### Persistência de Dados
Todos os dados são armazenados no banco de dados:
- Tentativas de recuperação
- Análises de IA
- Configurações por provedor
- Histórico de mensagens enviadas

## 📈 Métricas Disponíveis

- **Total de Tentativas**: Número total de tentativas de recuperação
- **Recuperações Bem-sucedidas**: Clientes que retornaram após recuperação
- **Taxa de Conversão**: Percentual de sucesso das tentativas
- **Tempo de Resposta**: Tempo médio para resposta do cliente
- **Análise por Período**: Métricas por dia, semana ou mês

## 🛡️ Segurança

- **Autenticação Obrigatória**: Todos os endpoints requerem token de autenticação
- **Isolamento de Dados**: Cada provedor acessa apenas seus dados
- **Validação de Entrada**: Todos os parâmetros são validados
- **Logs de Auditoria**: Todas as ações são registradas

## 🎨 Interface do Usuário

### Termômetro Animado
- **Animação Gradual**: O arco preenche suavemente conforme a taxa de conversão
- **Porcentagem Central**: Taxa de conversão exibida no centro do arco
- **Cores Dinâmicas**: Verde para boa performance, amarelo para média, vermelho para baixa

### Cards de Estatísticas
- **Ícones Intuitivos**: Cada métrica tem seu ícone representativo
- **Valores em Tempo Real**: Atualizações automáticas via API
- **Layout Responsivo**: Adapta-se a diferentes tamanhos de tela

### Lista de Conversas
- **Status Visual**: Cores diferentes para cada status (enviada, recuperada, falhou)
- **Informações Detalhadas**: Nome, telefone, motivo da recuperação
- **Histórico Completo**: Todas as tentativas de recuperação

## 🔄 Fluxo de Funcionamento

1. **Análise**: IA analisa conversas encerradas dos últimos dias
2. **Identificação**: Identifica clientes com potencial de recuperação
3. **Geração**: Cria mensagem personalizada baseada na análise
4. **Envio**: Envia mensagem via WhatsApp através do Uazapi
5. **Acompanhamento**: Registra tentativa e aguarda resposta
6. **Métricas**: Atualiza estatísticas e dashboard

## 📝 Exemplos de Uso

### Análise Manual
```bash
# Analisar conversas dos últimos 7 dias
python manage.py run_recovery_analysis --days-back 7

# Enviar mensagens de recuperação
python manage.py run_recovery_analysis --days-back 7 --send-messages

# Análise para provedor específico
python manage.py run_recovery_analysis --provider-id 1 --days-back 7
```

### API REST
```javascript
// Buscar estatísticas
const stats = await fetch('/api/recovery/stats/?provedor_id=1', {
  headers: { 'Authorization': 'Token ' + token }
});

// Enviar campanha
const campaign = await fetch('/api/recovery/campaign/', {
  method: 'POST',
  headers: { 
    'Authorization': 'Token ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ days_back: 7 })
});
```

## 🎯 Benefícios

- **Aumento de Vendas**: Recupera clientes que demonstraram interesse
- **Automatização**: Reduz trabalho manual de reativação
- **Personalização**: Mensagens adaptadas a cada situação
- **Métricas Precisas**: Acompanhamento detalhado da performance
- **Isolamento**: Cada provedor gerencia seus próprios dados
- **Escalabilidade**: Funciona com qualquer número de provedores
