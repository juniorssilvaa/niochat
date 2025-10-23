// Configuração de ambiente - Separação entre desenvolvimento e produção

const isDevelopment = process.env.NODE_ENV === 'development' || process.env.VITE_ENV === 'development'

export const config = {
  // URLs baseadas no ambiente
  baseUrl: isDevelopment 
    ? 'https://front.niochat.com.br'  // DESENVOLVIMENTO
    : 'https://app.niochat.com.br',   // PRODUÇÃO
  
  // Configurações de API
  apiUrl: isDevelopment 
    ? 'http://localhost:8010'  // DESENVOLVIMENTO
    : 'https://app.niochat.com.br',  // PRODUÇÃO
  
  // Configurações de WebSocket
  wsUrl: isDevelopment 
    ? 'ws://localhost:8010'  // DESENVOLVIMENTO
    : 'wss://app.niochat.com.br',  // PRODUÇÃO
  
  // Configurações de mídia
  mediaUrl: isDevelopment 
    ? 'http://localhost:8010'  // DESENVOLVIMENTO
    : 'https://app.niochat.com.br',  // PRODUÇÃO
}

// Função para construir URLs de mídia
export const buildMediaUrl = (fileUrl) => {
  if (!fileUrl) return null
  
  // Se já é uma URL completa, retorna como está
  if (fileUrl.startsWith('http')) {
    return fileUrl
  }
  
  // Constrói URL baseada no ambiente
  return `${config.mediaUrl}${fileUrl}`
}

// Função para construir URLs de API
export const buildApiUrl = (endpoint) => {
  return `${config.apiUrl}${endpoint}`
}

// Função para construir URLs de WebSocket
export const buildWsUrl = (endpoint) => {
  return `${config.wsUrl}${endpoint}`
}

export default config
