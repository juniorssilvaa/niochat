/**
 * Utilitário para autenticação WebSocket segura
 * Não expõe tokens em logs ou builds
 */

export const createAuthenticatedWebSocket = (url) => {
  try {
    const token = localStorage.getItem('token');
    const authenticatedUrl = token ? `${url}?token=${token}` : url;
    return new WebSocket(authenticatedUrl);
  } catch (error) {
    console.error('Erro ao criar WebSocket autenticado');
    return new WebSocket(url);
  }
};

export const getWebSocketUrl = (baseUrl) => {
  try {
    const token = localStorage.getItem('token');
    return token ? `${baseUrl}?token=${token}` : baseUrl;
  } catch (error) {
    return baseUrl;
  }
};
