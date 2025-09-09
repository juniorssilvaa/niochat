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
    if (!user || !user.id) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    // Fechar conexão anterior se existir
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.close();
    }

    try {
      // Conectar ao WebSocket individual do usuário na porta do Django
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${wsProtocol}://${window.location.hostname}:8010/ws/user/${user.id}/?token=${token}`;
      
      console.log(`🔗 Conectando WebSocket do usuário ${user.username}:`, wsUrl);
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`✅ WebSocket do usuário ${user.username} conectado`);
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
            console.log(`🏓 Pong recebido do usuário ${user.username}`);
          }
        } catch (error) {
          console.warn('Erro ao processar mensagem WebSocket do usuário:', error);
        }
      };
      
      ws.onclose = () => {
        console.log(`🔌 WebSocket do usuário ${user.username} desconectado`);
        websocketRef.current = null;
        
        // Limpar ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
        
        // Reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`🔄 Tentando reconectar WebSocket do usuário ${user.username}...`);
          connectUserWebSocket();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error(`❌ Erro WebSocket do usuário ${user.username}:`, error);
      };
      
    } catch (error) {
      console.error('Erro ao conectar WebSocket do usuário:', error);
    }
  };

  // Conectar quando o usuário for definido
  useEffect(() => {
    if (user && user.id) {
      connectUserWebSocket();
    }

    // Cleanup ao desmontar ou trocar usuário
    return () => {
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
  }, [user?.id]);

  // Não renderiza nada - é apenas um gerenciador de estado
  return null;
}

export default UserStatusManager;



