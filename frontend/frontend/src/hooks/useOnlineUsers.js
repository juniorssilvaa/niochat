import { useState, useEffect, useRef } from 'react';

export default function useOnlineUsers() {
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [websocket, setWebsocket] = useState(null);
  const reconnectTimeoutRef = useRef(null);

  // Função para verificar se um usuário está online
  const isUserOnline = (userId) => {
    return onlineUsers.has(userId);
  };

  // Função para obter a contagem de usuários online
  const getOnlineCount = () => {
    return onlineUsers.size;
  };

  // Função para buscar usuários online via API REST (fallback)
  const fetchOnlineUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('/api/users/', {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const users = data.results || data;
        const onlineUserIds = users
          .filter(user => user.is_online)
          .map(user => user.id);
        setOnlineUsers(new Set(onlineUserIds));
        console.log('👥 Status online atualizado via API:', onlineUserIds);
      }
    } catch (error) {
      console.warn('Erro ao buscar usuários online via API:', error);
    }
  };

  // Conectar ao WebSocket para monitorar usuários online em tempo real
  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    // Fechar WebSocket anterior se existir
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close();
    }

    try {
      // Conectar ao WebSocket correto na porta do Django (8010)
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${wsProtocol}://${window.location.host}/ws/user_status/?token=${token}`;
      
      console.log('Conectando ao WebSocket de status');
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket de status conectado');
        setWebsocket(ws);
        
        // Buscar status inicial via API
        fetchOnlineUsers();
        
        // Limpar timeout de reconexão
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Mensagem WebSocket status:', data);
          
          if (data.type === 'user_status_update' && data.users) {
            const onlineUserIds = data.users
              .filter(u => u.is_online)
              .map(u => u.id);
            setOnlineUsers(new Set(onlineUserIds));
            console.log('👥 Status online atualizado via WebSocket:', onlineUserIds);
          }
        } catch (error) {
          console.warn('Erro ao processar mensagem WebSocket:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket de status desconectado');
        setWebsocket(null);
        
        // Reconectar após 5 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Tentando reconectar WebSocket...');
          connectWebSocket();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('Erro WebSocket status:', error);
      };
      
    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
      // Fallback para API REST
      fetchOnlineUsers();
    }
  };

  // Inicializar sistema de status online
  useEffect(() => {
    // Aguardar um pouco para garantir que o sistema esteja totalmente carregado
    const timer = setTimeout(() => {
      connectWebSocket();
    }, 2000);
    
    // Buscar via API a cada 30 segundos como fallback
    const apiInterval = setInterval(fetchOnlineUsers, 30000);

    // Cleanup
    return () => {
      clearTimeout(timer);
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      clearInterval(apiInterval);
    };
  }, []);

  return {
    isUserOnline,
    getOnlineCount,
    onlineUsers: Array.from(onlineUsers)
  };
}