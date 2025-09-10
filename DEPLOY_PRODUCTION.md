# 🚀 Deploy para Produção - NioChat

## 📋 Configuração Atual

### **Portas:**
- **Frontend**: `8012` (serve na porta 3000)
- **Backend**: `8010` (Gunicorn na porta 8000)
- **PostgreSQL**: `5432` (interno)

### **Domínio:**
- **Acesso único**: `https://app.niochat.com.br`
- **API**: `https://app.niochat.com.br/api/*`
- **Admin**: `https://app.niochat.com.br/admin/*`
- **Media**: `https://app.niochat.com.br/media/*`

## 🔧 Configuração do Traefik

### **Rotas configuradas:**
```yaml
# API (prioridade 100)
- "traefik.http.routers.niochat-api.rule=Host(`app.niochat.com.br`) && PathPrefix(`/api`)"

# Admin (prioridade 100)
- "traefik.http.routers.niochat-admin.rule=Host(`app.niochat.com.br`) && PathPrefix(`/admin`)"

# Media (prioridade 100)
- "traefik.http.routers.niochat-media.rule=Host(`app.niochat.com.br`) && PathPrefix(`/media`)"

# Token Auth (prioridade 100)
- "traefik.http.routers.niochat-token-auth.rule=Host(`app.niochat.com.br`) && PathPrefix(`/api-token-auth`)"

# Frontend (prioridade 1 - catch-all)
- "traefik.http.routers.niochat-frontend.rule=Host(`app.niochat.com.br`)"
```

## 🚀 Deploy no Portainer

### **1. Deploy Automático:**
```bash
./deploy-portainer-production.sh
```

### **2. Deploy Manual:**
1. Acesse: `https://portainer.niochat.com.br`
2. Vá para **Stacks**
3. Clique em **"Add stack"**
4. Nome: `niochat`
5. Cole o conteúdo de `docker-compose-production.yml`
6. Clique em **"Deploy the stack"**

## 🔐 Credenciais

### **Superusuário:**
- **Usuário**: `Junior`
- **Senha**: `Semfim01@`

### **Banco de dados:**
- **Host**: `postgres` (interno)
- **Porta**: `5432`
- **Database**: `niochat`
- **Usuário**: `niochat_user`
- **Senha**: `E0sJT3wAYFuahovmHkxgy`

## 📊 Monitoramento

### **Logs:**
```bash
# Backend
docker logs niochat_niochat-backend.1.xxx

# Frontend
docker logs niochat_niochat-frontend.1.xxx

# PostgreSQL
docker logs niochat_postgres.1.xxx
```

### **Status dos containers:**
```bash
docker ps | grep niochat
```

## 🔄 Atualizações

### **1. Via GitHub Actions (Automático):**
- Push para `main` → Build automático → Deploy automático

### **2. Manual:**
```bash
# 1. Fazer commit das mudanças
git add .
git commit -m "feat: Nova funcionalidade"
git push origin main

# 2. Aguardar build no GitHub Actions
# 3. Executar deploy
./deploy-portainer-production.sh
```

## 🛠️ Troubleshooting

### **Problema: Tela branca**
- Verificar se o Traefik está roteando corretamente
- Verificar logs do frontend
- Verificar se a API está respondendo

### **Problema: Login não funciona**
- Verificar se o backend está rodando
- Verificar se o superusuário foi criado
- Verificar logs do backend

### **Problema: Arquivos estáticos não carregam**
- Verificar se o frontend está servindo na porta 3000
- Verificar se o Traefik está roteando para a porta correta

## 📁 Arquivos importantes

- `docker-compose-production.yml` - Stack para Portainer
- `Dockerfile.frontend` - Build do frontend
- `Dockerfile.backend` - Build do backend
- `deploy-portainer-production.sh` - Script de deploy
- `.github/workflows/deploy.yml` - CI/CD

## 🌐 URLs de acesso

- **Aplicação**: https://app.niochat.com.br
- **Portainer**: https://portainer.niochat.com.br
- **GitHub Actions**: https://github.com/Juniorsilvacmd/niotchat/actions
