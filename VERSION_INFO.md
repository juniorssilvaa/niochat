# NioChat - Informações de Versão

## Versão Atual: 2.8.12

### Data de Lançamento: 11/09/2025

### Funcionalidades desta Versão:
- Sistema de memória Redis para não pedir CPF repetidamente
- Envio automático de fatura via WhatsApp com botões interativos
- Verificação obrigatória se é cliente antes de prosseguir
- Uso automático das ferramentas GetCpfContato e SalvarCpfContato
- Fluxo inteligente para faturas: CPF → SGP → Geração → Envio automático

### Arquivos de Versão Atualizados:
- VERSION: 2.8.12
- frontend/frontend/package.json: 2.8.12
- frontend/frontend/package-lock.json: 2.8.12
- frontend/frontend/pnpm-lock.yaml: 2.8.12
- backend/niochat/settings.py: 2.8.12
- backend/core/telegram_service.py: 2.8.12
- CHANGELOG.json: 2.8.12

### Como Usar:
Para atualizar a versão automaticamente, execute:
```bash
python version_manager.py [major|minor|patch]
```

### Histórico de Versões:
- 2.1.0: IA Inteligente com Memória Redis e Envio Automático de Fatura
- 2.0.0: Integração ChatGPT + SGP Automático
- 1.0.0: Sistema base completo
