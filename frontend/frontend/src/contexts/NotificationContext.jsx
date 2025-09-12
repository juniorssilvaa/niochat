import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

export const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications deve ser usado dentro de NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const websocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [unreadMessagesByUser, setUnreadMessagesByUser] = useState({});
  
  // WebSocket para notificações do chat interno
  const internalChatWsRef = useRef(null);
  const [internalChatUnreadCount, setInternalChatUnreadCount] = useState(0);
  const [internalChatUnreadByUser, setInternalChatUnreadByUser] = useState({});
  const initializingRef = useRef(false);
  // Novos refs para eventos globais de conversas
  const painelWsRef = useRef(null);
  const painelReconnectRef = useRef(null);
  const soundEnabledRef = useRef(false);
  const newMsgSoundRef = useRef('mixkit-bell-notification-933.wav');
  const newConvSoundRef = useRef('mixkit-digital-quick-tone-2866.wav');
  const audioRef = useRef(null);
  const faviconTimerRef = useRef(null);
  const isFaviconBlinkingRef = useRef(false);

  // Carregar estado inicial do localStorage
  useEffect(() => {
    try {
      // Limpar TODOS os dados relacionados ao chat interno
      const keysToRemove = [
        'unread_messages_by_user',
        'internal_chat_unread_count',
        'internal_chat_unread_by_user',
        'chat_rooms',
        'internal_chat_messages',
        'internal_chat_participants',
        'internal_chat_data'
      ];
      
      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
      });
      
      // Zerar todos os contadores
      setUnreadCount(0);
      setHasNewMessages(false);
      setUnreadMessagesByUser({});
      setInternalChatUnreadCount(0);
      setInternalChatUnreadByUser({});
      
      console.log('🧹 localStorage e sessionStorage limpos');
    } catch (error) {
      console.error('Erro ao limpar notificações do localStorage:', error);
    }
  }, []);

  // Carregar usuário atual
  useEffect(() => {
    loadCurrentUser();
  }, []);

  // Conectar WebSocket quando usuário for carregado
  useEffect(() => {
    if (currentUser?.id) {
      connectWebSocket();
      connectPainelWebSocket();
      connectInternalChatWebSocket();
      loadInternalChatUnreadCount();
      loadInternalChatUnreadByUser();
    }

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (painelWsRef.current) {
        painelWsRef.current.close();
      }
      if (painelReconnectRef.current) {
        clearTimeout(painelReconnectRef.current);
      }
      if (internalChatWsRef.current) {
        internalChatWsRef.current.close();
      }
    };
  }, [currentUser?.id]);

  const loadCurrentUser = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('/api/auth/me/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData);
        // Carregar preferências de som do backend
        soundEnabledRef.current = !!userData.sound_notifications_enabled;
        if (userData.new_message_sound) newMsgSoundRef.current = userData.new_message_sound;
        if (userData.new_conversation_sound) newConvSoundRef.current = userData.new_conversation_sound;
      }
    } catch (error) {
      console.error('Erro ao carregar usuário atual:', error);
    }
  };

  const loadInternalChatUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/internal-chat-unread-count/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const count = data.total_unread || 0;
        setInternalChatUnreadCount(count);
        
        // Se não há mensagens não lidas, limpar localStorage também
        if (count === 0) {
          localStorage.removeItem('internal_chat_unread_count');
        }
      }
    } catch (error) {
      console.error('Erro ao carregar contador do chat interno:', error);
      // Em caso de erro, zerar o contador
      setInternalChatUnreadCount(0);
    }
  };

  const loadInternalChatUnreadByUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/internal-chat-unread-by-user/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setInternalChatUnreadByUser(data);
      }
    } catch (error) {
      console.error('Erro ao carregar contadores por usuário do chat interno:', error);
    }
  };

  const connectInternalChatWebSocket = () => {
    if (internalChatWsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Fechar conexão anterior se existir
    if (internalChatWsRef.current && internalChatWsRef.current.readyState !== WebSocket.CLOSED) {
      internalChatWsRef.current.close();
    }

    try {
      const token = localStorage.getItem('token');
      const wsUrl = `wss://${window.location.host}/ws/internal-chat-notifications/?token=${token}`;
      
      internalChatWsRef.current = new WebSocket(wsUrl);
      
      internalChatWsRef.current.onopen = () => {
        console.log('WebSocket do chat interno conectado');
        
        // Enviar mensagem de join
        internalChatWsRef.current.send(JSON.stringify({
          type: 'join_notifications'
        }));
      };
      
      internalChatWsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'unread_count_update') {
            setInternalChatUnreadCount(data.total_unread || 0);
            if (data.unread_by_user) {
              setInternalChatUnreadByUser(data.unread_by_user);
            }
          }
        } catch (error) {
          console.error('Erro ao processar mensagem WebSocket do chat interno:', error);
        }
      };
      
      internalChatWsRef.current.onclose = () => {
        console.log('WebSocket do chat interno desconectado');
        
        // Reconectar automaticamente após 3 segundos
        setTimeout(() => {
          if (currentUser?.id) {
            connectInternalChatWebSocket();
          }
        }, 3000);
      };
      
      internalChatWsRef.current.onerror = (error) => {
        console.error('Erro no WebSocket do chat interno:', error);
      };
      
    } catch (error) {
      console.error('Erro ao criar WebSocket do chat interno:', error);
    }
  };

  const connectWebSocket = () => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Fechar conexão anterior se existir
    if (websocketRef.current && websocketRef.current.readyState !== WebSocket.CLOSED) {
      websocketRef.current.close();
    }

    try {
      const token = localStorage.getItem('token');
      // Conectar ao WebSocket de chat privado para notificações
      const wsUrl = `wss://${window.location.host}/ws/private-chat/?token=${token}`;
      
      websocketRef.current = new WebSocket(wsUrl);
      
      websocketRef.current.onopen = () => {
        setIsConnected(true);
        
        // Aguardar currentUser estar disponível antes de enviar join_notifications
        if (currentUser?.id) {
          websocketRef.current.send(JSON.stringify({
            type: 'join_notifications',
            user_id: currentUser.id
          }));
        }
      };
      
      websocketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'new_private_message') {
            // Verificar se a mensagem é para o usuário atual
            if (data.message.recipient_id === currentUser.id) {
              const senderId = data.message.sender?.id?.toString();
              // Atualizar contador global
              setUnreadCount(prev => prev + 1);
              setHasNewMessages(true);
              // Atualizar contador por usuário
              if (senderId) {
                setUnreadMessagesByUser(prev => {
                  const newUnreadByUser = {
                    ...prev,
                    [senderId]: (prev[senderId] || 0) + 1
                  };
                  // Salvar no localStorage para sincronizar entre componentes
                  localStorage.setItem('unread_messages_by_user', JSON.stringify(newUnreadByUser));
                  // Disparar evento para sincronizar componentes
                  window.dispatchEvent(new Event('unread-messages-changed'));
                  return newUnreadByUser;
                });
              }
              // Notificação do navegador
              if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Nova Mensagem no Chat Interno', {
                  body: `${data.message.sender?.name || 'Usuario'}: ${data.message.content}`,
                  icon: '/favicon.ico',
                  tag: 'chat-interno'
                });
              }
            }
          } else if (data.type === 'notifications_joined') {
            // noop
          }
        } catch (error) {
          console.error('Erro ao processar notificacao:', error);
        }
      };
      
      websocketRef.current.onclose = (event) => {
        setIsConnected(false);
        // Reconectar automaticamente
        if (!event.wasClean) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (currentUser?.id) {
              connectWebSocket();
            }
          }, 3000);
        }
      };
      
      websocketRef.current.onerror = (error) => {
        console.error('Erro WebSocket global:', error);
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('Erro ao criar WebSocket global:', error);
    }
  };

  // WS global do painel para tocar som e piscar favicon em qualquer página
  const connectPainelWebSocket = () => {
    try {
      if (!currentUser?.provedor_id) return;
      const token = localStorage.getItem('token');
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${wsProtocol}://${window.location.host}/ws/painel/${currentUser.provedor_id}/?token=${token}`;
      if (painelWsRef.current?.readyState === WebSocket.OPEN) return;
      if (painelWsRef.current && painelWsRef.current.readyState !== WebSocket.CLOSED) {
        painelWsRef.current.close();
      }
      const ws = new WebSocket(wsUrl);
      painelWsRef.current = ws;
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const evt = data.type || data.event_type || data.action;
          if (evt === 'new_message' || evt === 'message' || evt === 'chat_message' || evt === 'message_created' || evt === 'messages') {
            playSound(newMsgSoundRef.current);
            startBlinkingFavicon();
          } else if (evt === 'conversation_created' || evt === 'conversation_updated' || evt === 'conversation_event' || evt === 'update_conversation') {
            playSound(newConvSoundRef.current);
            startBlinkingFavicon();
          }
        } catch (_) {}
      };
      ws.onclose = () => {
        painelReconnectRef.current = setTimeout(connectPainelWebSocket, 3000);
      };
      ws.onerror = () => {
        try { ws.close(); } catch (_) {}
      };
    } catch (e) {
      console.error('Erro ao abrir WS painel global:', e);
    }
  };

  const playSound = (fileName) => {
    if (!soundEnabledRef.current) return;
    try {
      const src = `/sounds/${fileName}`;
      if (!audioRef.current) {
        audioRef.current = new Audio(src);
      } else {
        audioRef.current.pause();
        audioRef.current.src = src;
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    } catch (_) {}
  };

  const setFavicon = (hrefBase) => {
    try {
      const href = `${hrefBase}?v=${Date.now()}`;
      const links = Array.from(document.querySelectorAll("link[rel~='icon']"));
      if (links.length > 0) {
        links.forEach(l => { l.href = href; });
      } else {
        const l1 = document.createElement('link');
        l1.rel = 'icon'; l1.type = 'image/x-icon'; l1.href = href; document.head.appendChild(l1);
        const l2 = document.createElement('link');
        l2.rel = 'shortcut icon'; l2.type = 'image/x-icon'; l2.href = href; document.head.appendChild(l2);
      }
    } catch (_) {}
  };

  const startBlinkingFavicon = () => {
    if (isFaviconBlinkingRef.current) return;
    isFaviconBlinkingRef.current = true;
    const defaultIcon = '/favicon.ico';
    const notifyIcon = '/faviconnotifica.ico';
    let toggle = false;
    faviconTimerRef.current = setInterval(() => {
      if (document.visibilityState === 'visible') {
        stopBlinkingFavicon();
        return;
      }
      toggle = !toggle;
      setFavicon(toggle ? notifyIcon : defaultIcon);
    }, 800);
  };

  const stopBlinkingFavicon = () => {
    if (faviconTimerRef.current) {
      clearInterval(faviconTimerRef.current);
      faviconTimerRef.current = null;
    }
    isFaviconBlinkingRef.current = false;
    setFavicon('/favicon.ico');
  };

  // Funções para gerenciar notificações
  const clearNotifications = () => {
    setUnreadCount(0);
    setHasNewMessages(false);
    setUnreadMessagesByUser({});
    localStorage.removeItem('unread_messages_by_user');
    // Disparar evento para sincronizar componentes
    window.dispatchEvent(new Event('unread-messages-changed'));
  };

  const markAsRead = (count = null, userId = null) => {
    if (userId) {
      // Marcar como lida mensagens de um usuário específico
      setUnreadMessagesByUser(prev => {
        const userUnreadCount = prev[userId] || 0;
        const newUnreadByUser = { ...prev };
        delete newUnreadByUser[userId];
        // Atualizar contador global
        setUnreadCount(prevTotal => Math.max(0, prevTotal - userUnreadCount));
        // Salvar no localStorage
        localStorage.setItem('unread_messages_by_user', JSON.stringify(newUnreadByUser));
        // Disparar evento para sincronizar componentes
        window.dispatchEvent(new Event('unread-messages-changed'));
        return newUnreadByUser;
      });
    } else if (count !== null) {
      setUnreadCount(prev => Math.max(0, prev - count));
    } else {
      clearNotifications();
    }
  };

  // Conectar WebSocket quando component monta
  useEffect(() => {
    if (initializingRef.current) {
      return;
    }
    initializingRef.current = true;
    connectWebSocket();
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      initializingRef.current = false;
    };
  }, []);

  // Enviar join_notifications quando currentUser for carregado
  useEffect(() => {
    if (currentUser?.id && websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({
        type: 'join_notifications',
        user_id: currentUser.id
      }));
    }
  }, [currentUser]);

  // Solicitar permissão para notificações
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Parar piscar quando a aba ficar visível
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        stopBlinkingFavicon();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      stopBlinkingFavicon();
    };
  }, []);

  const value = {
    unreadCount,
    hasNewMessages,
    currentUser,
    isConnected,
    unreadMessagesByUser,
    internalChatUnreadCount,
    internalChatUnreadByUser,
    clearNotifications,
    markAsRead,
    websocket: websocketRef.current
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};