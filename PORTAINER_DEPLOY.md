# Deploy NioChat no Portainer

Este guia explica como fazer o deploy do NioChat no Portainer usando Docker Swarm.

## Pré-requisitos

- Portainer instalado e configurado
- Docker Swarm ativo
- Rede `nioNet` criada
- Volumes externos criados
- Traefik configurado como proxy reverso

## 1. Preparação do Ambiente

### Criar Rede
```bash
docker network create --driver overlay --attachable nioNet
```

### Criar Volumes
```bash
docker volume create niochat-media
docker volume create niochat-static
docker volume create niochat-postgres
```

## 2. Configuração das Variáveis de Ambiente

Crie um arquivo `.env` com as seguintes variáveis:

```bash
# Django Settings
SECRET_KEY=sua-chave-secreta-muito-longa-e-segura-aqui
POSTGRES_PASSWORD=senha-segura-do-postgres

# Email Configuration (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app

# OpenAI Configuration (opcional)
OPENAI_API_KEY=sua-chave-openai-aqui
```

## 3. Deploy no Portainer

### Método 1: Via Interface Web do Portainer

1. Acesse o Portainer: `https://portainer.niochat.com.br`
2. Vá em **Stacks** → **Add stack**
3. Nome: `niochat`
4. Cole o conteúdo do arquivo `docker-compose.yml`
5. Configure as variáveis de ambiente
6. Clique em **Deploy the stack**

### Método 2: Via Script Automatizado

```bash
# Configure sua API key do Portainer
export PORTAINER_API_KEY=sua-api-key-do-portainer

# Execute o script de deploy
./deploy-portainer.sh
```

## 4. Configuração do Traefik

O sistema já está configurado para usar o Traefik existente. Os domínios configurados são:

- **Frontend**: `app.niochat.com.br`
- **API**: `api.niochat.com.br`
- **Admin**: `admin.niochat.com.br`

## 5. Verificação do Deploy

Após o deploy, verifique se os serviços estão rodando:

```bash
# Verificar status dos containers
docker service ls | grep niochat

# Verificar logs
docker service logs niochat_backend
docker service logs niochat_frontend
```

## 6. Acesso ao Sistema

- **Frontend**: https://app.niochat.com.br
- **API**: https://api.niochat.com.br
- **Admin**: https://admin.niochat.com.br

### Credenciais Padrão do Superadmin
- **Usuário**: `Junior`
- **Senha**: `semfim01@`

## 7. Configuração Inicial

1. Acesse o admin: https://admin.niochat.com.br
2. Faça login com as credenciais padrão
3. Configure os provedores
4. Configure as integrações (Uazapi, SGP, etc.)
5. Crie usuários e equipes

## 8. CI/CD com GitHub Actions

O sistema está configurado para deploy automático via GitHub Actions:

1. **Push para main**: Dispara build e deploy automático
2. **Pull Request**: Executa testes
3. **Deploy**: Atualiza automaticamente o Portainer

### Configuração do GitHub Actions

1. Vá em **Settings** → **Secrets and variables** → **Actions**
2. Adicione os secrets:
   - `PORTAINER_API_KEY`: Sua API key do Portainer
   - `GITHUB_TOKEN`: Token do GitHub (gerado automaticamente)

## 9. Monitoramento

### Health Checks
- Backend: `https://api.niochat.com.br/api/health/`
- Frontend: `https://app.niochat.com.br/`

### Logs
```bash
# Logs do backend
docker service logs -f niochat_backend

# Logs do frontend
docker service logs -f niochat_frontend

# Logs do Celery
docker service logs -f niochat_celery
```

## 10. Backup e Restore

### Backup do Banco de Dados
```bash
# Backup
docker exec niochat_postgres pg_dump -U niochat_user niochat > backup.sql

# Restore
docker exec -i niochat_postgres psql -U niochat_user niochat < backup.sql
```

### Backup dos Volumes
```bash
# Backup media
docker run --rm -v niochat-media:/data -v $(pwd):/backup alpine tar czf /backup/media-backup.tar.gz -C /data .

# Restore media
docker run --rm -v niochat-media:/data -v $(pwd):/backup alpine tar xzf /backup/media-backup.tar.gz -C /data
```

## 11. Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Verificar logs
docker service logs niochat_backend

# Verificar recursos
docker service inspect niochat_backend
```

#### Banco de dados não conecta
```bash
# Verificar se o PostgreSQL está rodando
docker service ls | grep postgres

# Verificar logs do PostgreSQL
docker service logs niochat_postgres
```

#### Frontend não carrega
```bash
# Verificar se o Traefik está roteando corretamente
docker service logs traefik

# Verificar DNS
nslookup app.niochat.com.br
```

#### WebSocket não conecta
```bash
# Verificar se o Redis está rodando
docker service ls | grep redis

# Verificar logs do Redis
docker service logs redis
```

## 12. Atualizações

### Atualização Manual
```bash
# Pull das novas imagens
docker service update --image ghcr.io/juniorssilvaa/niochat-backend:latest niochat_backend
docker service update --image ghcr.io/juniorssilvaa/niochat-frontend:latest niochat_frontend
```

### Atualização Automática
O GitHub Actions fará o deploy automático quando houver push para a branch `main`.

## 13. Segurança

### Certificados SSL
O Traefik já está configurado para usar Let's Encrypt. Os certificados são gerados automaticamente.

### Firewall
Configure o firewall para permitir apenas as portas necessárias:
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH)

### Backup de Segurança
Configure backups automáticos dos volumes e banco de dados.

## 14. Performance

### Recursos Recomendados
- **CPU**: 4 cores
- **RAM**: 8GB
- **Disco**: 100GB SSD

### Otimizações
- Use volumes SSD para melhor performance
- Configure Redis com persistência
- Use CDN para arquivos estáticos

## 15. Suporte

Para suporte técnico:
- Abra uma issue no GitHub
- Entre em contato via email
- Consulte a documentação completa no README.md
