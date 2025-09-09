# Configuração do GitHub Actions com Portainer

Este guia explica como conectar o GitHub Actions ao Portainer para deploy automático.

## 🔧 **Passo 1: Configurar Secrets no GitHub**

### 1.1 Acessar as Configurações
1. Vá para: `https://github.com/Juniorsilvacmd/niotchat`
2. Clique em **Settings** (aba superior)
3. No menu lateral, clique em **Secrets and variables** → **Actions**

### 1.2 Adicionar Secrets
Clique em **"New repository secret"** e adicione:

#### **PORTAINER_API_KEY**
- **Name**: `PORTAINER_API_KEY`
- **Secret**: Sua API key do Portainer (veja como obter abaixo)

#### **GITHUB_TOKEN** (Opcional - já existe por padrão)
- **Name**: `GITHUB_TOKEN`
- **Secret**: Token do GitHub (gerado automaticamente)

## 🔑 **Passo 2: Obter API Key do Portainer**

### 2.1 Acessar o Portainer
1. Vá para: `https://portainer.niochat.com.br`
2. Faça login com suas credenciais

### 2.2 Criar API Key
1. Clique no seu **avatar** (canto superior direito)
2. Selecione **Account**
3. Vá para a aba **API Keys**
4. Clique em **"Add API Key"**
5. Preencha:
   - **Description**: `GitHub Actions Deploy`
   - **Expires**: `Never` (ou escolha uma data)
6. Clique em **"Add API Key"**
7. **Copie a chave gerada** (você só verá uma vez!)

### 2.3 Adicionar no GitHub
1. Volte ao GitHub → Settings → Secrets
2. Clique em **"New repository secret"**
3. **Name**: `PORTAINER_API_KEY`
4. **Secret**: Cole a chave copiada do Portainer
5. Clique em **"Add secret"**

## 🚀 **Passo 3: Criar Stack no Portainer**

### 3.1 Preparar o Ambiente
```bash
# Criar rede (se não existir)
docker network create --driver overlay --attachable nioNet

# Criar volumes (se não existirem)
docker volume create niochat-media
docker volume create niochat-static
docker volume create niochat-postgres
```

### 3.2 Criar Stack no Portainer
1. Acesse: `https://portainer.niochat.com.br`
2. Vá em **Stacks** → **Add stack**
3. Preencha:
   - **Name**: `niochat`
   - **Build method**: `Web editor`
4. Cole o conteúdo do arquivo `docker-compose.yml`
5. Configure as variáveis de ambiente:
   - `SECRET_KEY`: Sua chave secreta do Django
   - `POSTGRES_PASSWORD`: Senha segura para PostgreSQL
6. Clique em **"Deploy the stack"**

## ✅ **Passo 4: Testar o Deploy Automático**

### 4.1 Fazer um Push de Teste
```bash
# Fazer uma pequena alteração
echo "# Teste de deploy automático" >> README.md
git add README.md
git commit -m "test: Teste de deploy automático"
git push origin main
```

### 4.2 Verificar o GitHub Actions
1. Vá para: `https://github.com/Juniorsilvacmd/niotchat/actions`
2. Clique no workflow que está rodando
3. Acompanhe os logs em tempo real

### 4.3 Verificar o Portainer
1. Acesse: `https://portainer.niochat.com.br`
2. Vá em **Stacks** → **niochat**
3. Verifique se os containers foram atualizados

## 🔍 **Passo 5: Verificar o Deploy**

### 5.1 Health Checks
- **Backend**: https://api.niochat.com.br/api/health/
- **Frontend**: https://app.niochat.com.br/
- **Admin**: https://admin.niochat.com.br/

### 5.2 Logs do Portainer
1. Vá em **Stacks** → **niochat**
2. Clique em **"Logs"** para ver os logs dos containers
3. Verifique se não há erros

## 🛠️ **Troubleshooting**

### Problema: "Stack 'niochat' not found"
**Solução**: Crie a stack no Portainer primeiro (Passo 3)

### Problema: "API Key invalid"
**Solução**: 
1. Verifique se a API key está correta
2. Verifique se a API key não expirou
3. Crie uma nova API key se necessário

### Problema: "Permission denied"
**Solução**: 
1. Verifique se a API key tem permissões de admin
2. Verifique se o usuário tem acesso ao stack

### Problema: "Image not found"
**Solução**: 
1. Verifique se as imagens foram buildadas corretamente
2. Verifique se o GitHub Container Registry está acessível

## 📊 **Monitoramento**

### GitHub Actions
- **URL**: `https://github.com/Juniorsilvacmd/niotchat/actions`
- **Status**: Verde = sucesso, Vermelho = erro
- **Logs**: Clique no workflow para ver detalhes

### Portainer
- **URL**: `https://portainer.niochat.com.br`
- **Stacks**: Ver status dos containers
- **Logs**: Ver logs em tempo real

## 🔄 **Fluxo de Deploy**

1. **Push para main** → Dispara GitHub Actions
2. **Testes** → Executa testes automatizados
3. **Build** → Cria imagens Docker
4. **Push** → Envia imagens para GitHub Container Registry
5. **Deploy** → Atualiza stack no Portainer
6. **Health Check** → Verifica se aplicação está funcionando
7. **Notificação** → Confirma sucesso ou falha

## 🎯 **Próximos Passos**

Após configurar tudo:

1. **Teste o deploy** fazendo um push
2. **Verifique os logs** no GitHub Actions
3. **Confirme o funcionamento** acessando as URLs
4. **Configure notificações** (opcional)

## 📞 **Suporte**

Se encontrar problemas:

1. Verifique os logs do GitHub Actions
2. Verifique os logs do Portainer
3. Consulte a documentação do Portainer
4. Abra uma issue no GitHub

---

**✅ Após seguir todos os passos, o deploy automático estará funcionando!**
