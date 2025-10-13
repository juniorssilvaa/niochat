import { useEffect, useRef } from 'react';

/**
 * Componente para gerenciar o status online do usuário logado
 * Conecta ao WebSocket individual do usuário para marcar como online/offline automaticamente
 */
function UserStatusManager({ user }) {
  const websocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  const connectUserWebSocket = () => {
    if (!user || !user.id || !user.token) return;

    const token = user.token || localStorage.getItem('token');
    if (!token) return;

    // Fechar conexão anterior se existir
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.close();
    }

    try {
      // Conectar ao WebSocket individual do usuário na porta do Django
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const token = localStorage.getItem('token');
      const wsUrl = `${wsProtocol}://${window.location.host}/ws/user/${user.id}/?token=${token}`;
      
      // Log removido('Conectando WebSocket do usuário');
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        // Log removido para não expor dados sensíveis
        websocketRef.current = ws;
        
        // Limpar timeout de reconexão
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        
        // Enviar ping a cada 30 segundos para manter conexão ativa
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            // Pong recebido do usuário
          }
        } catch (error) {
          console.warn('Erro ao processar mensagem WebSocket do usuário:', error);
        }
      };
      
      ws.onclose = () => {
        // Log removido('WebSocket do usuário desconectado');
        websocketRef.current = null;
        
        // Limpar ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          // Log removido('Tentando reconectar WebSocket do usuário');
          connectUserWebSocket();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('Erro WebSocket: Conexão falhou');
      };
      
    } catch (error) {
      console.error('Erro ao conectar WebSocket');
    }
  };

  // Conectar quando o usuário for definido
  useEffect(() => {
    if (user && user.id && user.token) {
      // Aguardar um pouco para garantir que o usuário esteja totalmente carregado
      const timer = setTimeout(() => {
        connectUserWebSocket();
      }, 1000);
      
      return () => {
        clearTimeout(timer);
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          websocketRef.current.close();
        }
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
      };
    }
  }, [user?.id, user?.token]);

  // Não renderiza nada - é apenas um gerenciador de estado
  return null;
}

export default UserStatusManager;



