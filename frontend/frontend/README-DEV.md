# NioChat Frontend - Configuração de Desenvolvimento

## Configurações Disponíveis

### Produção (Padrão)
- **Arquivo**: `vite.config.js`
- **Uso**: Para build de produção
- **Características**: Sem proxy, usa URLs relativas, roteamento via Traefik

### Desenvolvimento Local
- **Arquivo**: `vite.config.local.js` (não commitado)
- **Uso**: Para desenvolvimento local
- **Características**: Proxy para `http://192.168.100.55:8010`

## Scripts Disponíveis

```bash
# Desenvolvimento (produção)
npm run dev

# Desenvolvimento local (com proxy)
npm run dev:local

# Build para produção
npm run build

# Build para produção (explícito)
npm run build:prod

# Preview do build
npm run preview
```

## Configuração de Desenvolvimento Local

Para usar a configuração local, copie o arquivo de exemplo:

```bash
cp vite.config.local.js.example vite.config.local.js
```

E ajuste as URLs conforme necessário.

## Arquivos Ignorados

O `.gitignore` está configurado para ignorar:
- `node_modules/`
- `dist/`
- `*.local.js`
- `*.backup`
- Arquivos de desenvolvimento local
- Logs e cache

## Produção

Em produção, o sistema usa:
- URLs relativas (`/api/`, `/ws/`, etc.)
- Roteamento via Traefik
- Sem proxy local
- Build otimizado
