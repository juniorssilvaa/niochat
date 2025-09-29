import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, Filter, MoreHorizontal, User, Clock, Tag, MoreVertical } from 'lucide-react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';

const ConversationList = ({ onConversationSelect, selectedConversation, provedorId, onConversationUpdate }) => {
  
  const [searchTerm, setSearchTerm] = useState(() => {
    return localStorage.getItem('conversationSearchTerm') || '';
  });
  
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('conversationListActiveTab') || 'mine';
  });
  
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userPermissions, setUserPermissions] = useState([]);
  const [user, setUser] = useState(null);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [newMessageNotification, setNewMessageNotification] = useState(false);
  const faviconTimerRef = useRef(null);
  const isFaviconBlinkingRef = useRef(false);
  const [lastUpdateTime, setLastUpdateTime] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const audioRef = useRef(null);
  const prevConversationsRef = useRef({}); // { [id]: lastMessageIdOrTime }
  const hasSoundInitRef = useRef(false);
  
  // # Debug logging removed for security Estados para novo atendimento
  const [showMenuAtendimento, setShowMenuAtendimento] = useState(false);
  const [modalNovoContato, setModalNovoContato] = useState(false);
  const [modalContatoExistente, setModalContatoExistente] = useState(false);
  
  const [novoContato, setNovoContato] = useState({
    nome: '',
    telefone: '',
    canal: 'whatsapp',
    mensagem: ''
  });
  
  const [contatoExistente, setContatoExistente] = useState({
    busca: '',
    contato: null,
    mensagem: ''
  });
  
  const [enviandoAtendimento, setEnviandoAtendimento] = useState(false);
  const [buscandoContato, setBuscandoContato] = useState(false);
  const [contatosEncontrados, setContatosEncontrados] = useState([]);
  
  // # Debug logging removed for security Função para buscar contatos existentes
  const buscarContatos = async (termo) => {
    if (!termo.trim()) {
      setContatosEncontrados([]);
      return;
    }

    setBuscandoContato(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await axios.get(`/api/contacts/?search=${termo}`, {
        headers: { Authorization: `Token ${token}` }
      });
      
      setContatosEncontrados(response.data.results || []);
    } catch (error) {
      console.error('Erro ao buscar contatos:', error);
      setContatosEncontrados([]);
    } finally {
      setBuscandoContato(false);
    }
  };

  // Removido prompt de desbloqueio (UX simplificada)
  useEffect(() => {}, [authReady, user?.sound_notifications_enabled]);

  // # Debug logging removed for security Função para criar atendimento com novo contato
  const handleNovoContato = async () => {
    if (!novoContato.nome || !novoContato.telefone || !novoContato.mensagem) {
      alert('Por favor, preencha todos os campos');
      return;
    }

    const telefoneFormatado = novoContato.telefone.replace(/\D/g, '');
    if (!telefoneFormatado.startsWith('55') || telefoneFormatado.length < 12) {
      alert('Telefone deve começar com 55 e ter pelo menos 12 dígitos');
      return;
    }

    setEnviandoAtendimento(true);
    const token = localStorage.getItem('token');

    try {
      // # Debug logging removed for security USAR ENDPOINT COMPLETO que faz tudo
      const userResponse = await axios.get('/api/auth/me/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      // 1. Criar ou buscar contato
      let contactResponse;
      try {
        contactResponse = await axios.post('/api/contacts/', {
          name: novoContato.nome,
          phone: telefoneFormatado,
          provedor: 2
        }, {
          headers: { Authorization: `Token ${token}` }
        });
      } catch (error) {
        if (error.response?.status === 400 && error.response?.data?.non_field_errors?.[0]?.includes('único')) {
          // Contato já existe, buscar o existente
          const contactsResponse = await axios.get(`/api/contacts/?phone=${telefoneFormatado}`, {
            headers: { Authorization: `Token ${token}` }
          });
          contactResponse = { data: contactsResponse.data.results[0] };
        } else {
          throw error;
        }
      }

      // 2. Buscar inbox padrão para o canal
      const inboxesResponse = await axios.get('/api/inboxes/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      const inbox = inboxesResponse.data.results.find(
        inbox => inbox.channel_type === novoContato.canal
      ) || inboxesResponse.data.results[0];

      if (!inbox) {
        throw new Error('Nenhum inbox encontrado');
      }

      // 3. Criar conversa
      const conversationResponse = await axios.post('/api/conversations/', {
        contact_id: contactResponse.data.id,
        inbox_id: inbox.id,
        assignee_id: userResponse.data.id,
        status: 'open'
      }, {
        headers: { Authorization: `Token ${token}` }
      });

      // 4. Enviar mensagem inicial
      const messageResponse = await axios.post('/api/messages/send_text/', {
        content: novoContato.mensagem,
        conversation_id: conversationResponse.data.id
      }, {
        headers: { Authorization: `Token ${token}` }
      });

      alert('Atendimento criado com sucesso! Aparecerá no painel em instantes.');
      setNovoContato({ nome: '', telefone: '', canal: 'whatsapp', mensagem: '' });
      setModalNovoContato(false);
      
      // Recarregar conversas
      setTimeout(() => fetchConversations(true), 1000);
      
    } catch (error) {
      console.error('Erro ao criar novo contato:', error);
      alert('Erro ao enviar mensagem: ' + (error.response?.data?.detail || error.message));
    } finally {
      setEnviandoAtendimento(false);
    }
  };

  // # Debug logging removed for security Função para criar atendimento com contato existente
  const handleContatoExistente = async () => {
    if (!contatoExistente.contato || !contatoExistente.mensagem) {
      alert('Por favor, selecione um contato e digite a mensagem');
      return;
    }

    setEnviandoAtendimento(true);
    const token = localStorage.getItem('token');

    try {
      // # Debug logging removed for security USAR ENDPOINT COMPLETO para contato existente
      const userResponse = await axios.get('/api/auth/me/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      // 1. Buscar inbox padrão
      const inboxesResponse = await axios.get('/api/inboxes/', {
        headers: { Authorization: `Token ${token}` }
      });
      
      const inbox = inboxesResponse.data.results.find(
        inbox => inbox.channel_type === 'whatsapp'
      ) || inboxesResponse.data.results[0];

      if (!inbox) {
        throw new Error('Nenhum inbox encontrado');
      }

      // 2. Criar conversa
      const conversationResponse = await axios.post('/api/conversations/', {
        contact_id: contatoExistente.contato.id,
        inbox_id: inbox.id,
        assignee_id: userResponse.data.id,
        status: 'open'
      }, {
        headers: { Authorization: `Token ${token}` }
      });

      // 3. Enviar mensagem inicial
      const messageResponse = await axios.post('/api/messages/send_text/', {
        content: contatoExistente.mensagem,
        conversation_id: conversationResponse.data.id
      }, {
        headers: { Authorization: `Token ${token}` }
      });

      alert('Atendimento criado com contato existente! Aparecerá no painel em instantes.');
      setContatoExistente({ busca: '', contato: null, mensagem: '' });
      setModalContatoExistente(false);
      setContatosEncontrados([]);
      
      // Recarregar conversas
      setTimeout(() => fetchConversations(true), 1000);
      
    } catch (error) {
      console.error('Erro ao enviar para contato existente:', error);
      alert('Erro ao enviar mensagem: ' + (error.response?.data?.detail || error.message));
    } finally {
      setEnviandoAtendimento(false);
    }
  };

  // Ref para verificar se o componente está montado
  const isMounted = useRef(true);
  const wsRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  
  // Cleanup quando o componente desmontar
  useEffect(() => {
    isMounted.current = true;
    
    return () => {
      isMounted.current = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  // Salvar termo de busca no localStorage
  useEffect(() => {
    localStorage.setItem('conversationSearchTerm', searchTerm);
  }, [searchTerm]);

  // Salvar aba ativa no localStorage
  useEffect(() => {
    localStorage.setItem('conversationListActiveTab', activeTab);
  }, [activeTab]);

  // Função para verificar se há sessão ativa do Django
  const checkDjangoSession = async () => {
    try {
      console.log('# Debug logging removed for security Verificando sessão Django...');
      const response = await axios.get('/admin/', {
        withCredentials: true,
        maxRedirects: 0,
        validateStatus: (status) => status < 400
      });
      
      // Se retornou HTML da página admin, provavelmente está logado
      if (response.data && typeof response.data === 'string' && response.data.includes('Logout')) {
        console.log('# Debug logging removed for security Sessão Django ativa detectada');
        return true;
      }
      
      return false;
    } catch (error) {
      if (error.response?.status === 302) {
        // Redirecionamento indica que não está logado
        return false;
      }
      console.log('# Debug logging removed for security Erro ao verificar sessão Django:', error.message);
      return false;
    }
  };

  // Função para verificar e fazer login automático
  const checkAuthAndLogin = async () => {
    console.log('Verificando autenticação...');
    
    try {
      const token = localStorage.getItem('token');
      console.log('Credenciais verificadas no localStorage');
      if (token) {
        const userRes = await axios.get('/api/auth/me/', {
          headers: { Authorization: `Token ${token}` }
        });
        
        if (isMounted.current) {
          setUser(userRes.data);
          setUserPermissions(userRes.data.permissions || []);
          setAuthReady(true);
          console.log('Usuário autenticado com sucesso');
          return true;
        }
      } else {
        console.log('Nenhuma credencial encontrada no localStorage');
      }
    } catch (error) {
      console.log('# Debug logging removed for security Token inválido ou expirado:', error.message);
      console.log('# Debug logging removed for security Detalhes do erro:', error.response?.data);
      localStorage.removeItem('token');
    }
    
    // Se não há token válido, verificar se há usuário logado na sessão
    try {
      console.log('# Debug logging removed for security Verificando sessão ativa...');
      const userRes = await axios.get('/api/auth/me/', {
        withCredentials: true // Incluir cookies de sessão
      });
      
      if (isMounted.current) {
        setUser(userRes.data);
        setUserPermissions(userRes.data.permissions || []);
        setAuthReady(true);
        console.log('Usuário logado via sessão');
        console.log('# Debug logging removed for security AuthReady definido como true via sessão');
        return true;
      }
    } catch (error) {
      console.log('# Debug logging removed for security Nenhuma sessão ativa encontrada', error.message);
      
      // Tentar verificar sessão Django como último recurso
      const hasDjangoSession = await checkDjangoSession();
      if (hasDjangoSession) {
        console.log('# Debug logging removed for security Sessão Django detectada, tentando obter dados do usuário...');
        // Aqui você pode implementar uma chamada para obter dados do usuário da sessão Django
        // Por enquanto, vamos marcar como autenticado
        if (isMounted.current) {
          setAuthReady(true);
          setHasInitialized(true);
          console.log('# Debug logging removed for security AuthReady definido como true via Django session');
          return true;
        }
      }
    }
    
    // Se chegou aqui, não há autenticação válida
    console.log('⚠️ Nenhuma autenticação válida encontrada');
    if (isMounted.current) {
      setHasInitialized(true);
    }
    return false;
  };

  // Preferências de som
  const isSoundEnabled = () => {
    if (typeof user?.sound_notifications_enabled === 'boolean') return user.sound_notifications_enabled;
    return localStorage.getItem('sound_notifications_enabled') === 'true';
  };
  const getNewMessageSound = () => {
    return user?.new_message_sound || localStorage.getItem('sound_new_message') || 'mixkit-bell-notification-933.wav';
  };
  const getNewConversationSound = () => {
    return user?.new_conversation_sound || localStorage.getItem('sound_new_conversation') || 'mixkit-digital-quick-tone-2866.wav';
  };
  const playSound = (fileName) => {
    if (!isSoundEnabled()) return;
    try {
      const src = `/sounds/${fileName}`;
      if (!audioRef.current) {
        audioRef.current = new Audio(src);
      } else {
        audioRef.current.pause();
        audioRef.current.src = src;
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {
        // Autoplay bloqueado: solicitar interação do usuário
        setShowSoundPrompt(true);
      });
    } catch (e) {
      // Silenciar erros de autoplay
    }
  };

  const setFavicon = (hrefBase) => {
    try {
      const href = `${hrefBase}?v=${Date.now()}`; // cache-busting
      const links = Array.from(document.querySelectorAll("link[rel~='icon']"));
      if (links.length > 0) {
        links.forEach(l => { l.href = href; });
      } else {
        // Criar tanto 'icon' quanto 'shortcut icon' para compatibilidade
        const link1 = document.createElement('link');
        link1.rel = 'icon';
        link1.type = 'image/x-icon';
        link1.href = href;
        document.head.appendChild(link1);
        const link2 = document.createElement('link');
        link2.rel = 'shortcut icon';
        link2.type = 'image/x-icon';
        link2.href = href;
        document.head.appendChild(link2);
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
        // parar quando a aba estiver ativa
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

  const unlockAudio = () => {
    try {
      const src = `/sounds/${getNewMessageSound()}`;
      if (!audioRef.current) {
        audioRef.current = new Audio(src);
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play()
        .then(() => setShowSoundPrompt(false))
        .catch(() => setShowSoundPrompt(true));
    } catch (_) {}
  };

  // Função para buscar conversas
  const fetchConversations = async (forceRefresh = false) => {
    if (!isMounted.current || !authReady) {
      console.log('⚠️ Componente não montado ou auth não ready');
      return;
    }
    
    console.log('# Debug logging removed for security Buscando conversas...', { forceRefresh, provedorId, authReady });
    
    if (forceRefresh) {
      setLoading(true);
    }
    
    try {
      const token = localStorage.getItem('token');
      console.log('Credenciais encontradas');
      if (!token) {
        console.error('# Debug logging removed for security Token não encontrado');
        return;
      }

      // Buscar conversas sem filtro de provedor primeiro
      const res = await axios.get('/api/conversations/?page_size=100&ordering=-created_at', {
        headers: { Authorization: `Token ${token}` }
      });
      
      if (!isMounted.current) return;

      const conversationsData = res.data.results || res.data || [];
      
      // Filtrar conversas ativas (incluir mais status)
      const activeConversations = conversationsData.filter(conv => {
        const status = conv.status || conv.additional_attributes?.status;
        // Excluir apenas conversas explicitamente fechadas
        const closedStatuses = ['closed', 'encerrada', 'resolved', 'finalizada'];
        return !closedStatuses.includes(status);
      });
      
      // Detectar novas conversas e novas mensagens (fallback quando WS não tocar)
      try {
        const prevMap = prevConversationsRef.current || {};
        const nextMap = {};
        const seenIds = new Set();

        activeConversations.forEach(conv => {
          const convId = conv.id;
          const lastMsgKey = conv.last_message?.id || conv.last_message?.created_at || conv.updated_at || conv.created_at || 'none';
          nextMap[convId] = lastMsgKey;
          seenIds.add(convId);

          if (hasSoundInitRef.current) {
            if (!(convId in prevMap)) {
              // Nova conversa
              playSound(getNewConversationSound());
            } else if (prevMap[convId] !== lastMsgKey) {
              // Nova mensagem
              playSound(getNewMessageSound());
            }
          }
        });

        // Atualizar referência para próxima comparação
        prevConversationsRef.current = nextMap;
        if (!hasSoundInitRef.current) {
          hasSoundInitRef.current = true; // evitar tocar tudo na primeira carga
        }
      } catch (_) {}

      console.log('# Debug logging removed for security Conversas ativas encontradas:', activeConversations.length);

      setConversations(activeConversations);
      setHasInitialized(true);
      setLastUpdateTime(new Date());
      
    } catch (err) {
      if (isMounted.current) {
        console.error('# Debug logging removed for security Erro ao carregar conversas:', err);
        
        // Se o erro for de autenticação, tentar reautenticar
        if (err.response?.status === 401) {
          console.log('# Debug logging removed for security Erro de autenticação, tentando reautenticar...');
          setAuthReady(false);
          await checkAuthAndLogin();
        } else if (err.response?.status === 403) {
          console.log('🚫 Acesso negado, usuário não tem permissão para ver conversas');
          setConversations([]);
        } else {
          console.log('⚠️ Outro tipo de erro, definindo conversas vazias');
          setConversations([]);
        }
        
        setHasInitialized(true);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  };

  // Inicialização: Login automático
  useEffect(() => {
    const initializeAuth = async () => {
      const success = await checkAuthAndLogin();
      
      if (!success && isMounted.current) {
        setAuthReady(false);
        setHasInitialized(true);
      }
    };
    
    initializeAuth();
  }, []);

  // Buscar conversas quando auth estiver pronto
  useEffect(() => {
    if (authReady && isMounted.current) {
      console.log('# Debug logging removed for security Auth pronto, buscando conversas...');
      fetchConversations(true);
    }
  }, [authReady]);

  // Expor função de recarregamento
  useEffect(() => {
    if (onConversationUpdate && authReady) {
      onConversationUpdate(() => fetchConversations(true));
    }
  }, [onConversationUpdate, authReady]);

  // WebSocket para atualização em tempo real
  useEffect(() => {
    if (!provedorId || !authReady || !isMounted.current) {
      return;
    }

    console.log('# Debug logging removed for security Conectando WebSocket para provedor:', provedorId);
    
    const connectWebSocket = () => {
      const token = localStorage.getItem('token');
      const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/painel/${provedorId}/?token=${token}`);
      wsRef.current = ws;
      
      const wsTimeout = setTimeout(() => {
        console.log('Timeout do WebSocket');
        setWsConnected(false);
      }, 5000);
      
      ws.onopen = () => {
        console.log('# Debug logging removed for security WebSocket conectado');
        clearTimeout(wsTimeout);
        setWsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('# Debug logging removed for security WebSocket recebeu:', data);
          
          // Processar todos os tipos de eventos relacionados a conversas
          if (data.type === 'conversation_created' || 
              data.type === 'conversation_updated' || 
              data.type === 'conversation_event' ||
              data.type === 'new_message' ||
              data.type === 'message_created' ||
              data.type === 'message' ||
              data.type === 'chat_message' ||
              data.type === 'messages' ||
              data.event_type === 'new_message' ||
              data.event_type === 'conversation_updated' ||
              data.event_type === 'message' ||
              data.event_type === 'chat_message' ||
              data.event_type === 'messages') {
            // Tocar som e piscar favicon conforme o tipo de evento
            try {
              const evt = data.type || data.event_type;
              if (evt === 'new_message' || evt === 'message_created' || evt === 'message' || evt === 'chat_message' || evt === 'messages') {
                playSound(getNewMessageSound());
                startBlinkingFavicon();
              } else if (evt === 'conversation_created' || evt === 'conversation_updated' || evt === 'conversation_event') {
                const conv = data.conversation || data.payload || data.data;
                const status = conv?.status || conv?.additional_attributes?.status;
                const assignedToMe = conv?.assignee && user && (
                  (conv.assignee.id && conv.assignee.id === user.id) ||
                  (conv.assignee.username && conv.assignee.username === user.username)
                );
                const isUnassignedPending = !conv?.assignee && status === 'pending';
                if (!conv || assignedToMe || isUnassignedPending) {
                  playSound(getNewConversationSound());
                  startBlinkingFavicon();
                }
              }
            } catch (_) {}
            
            console.log('# Debug logging removed for security Atualização recebida via WebSocket, recarregando lista');
            setNewMessageNotification(true);
            setTimeout(() => setNewMessageNotification(false), 3000);
            
            // Recarregar conversas imediatamente
            setTimeout(() => fetchConversations(true), 0);
          }
        } catch (error) {
          console.error('# Debug logging removed for security Erro ao processar mensagem WebSocket:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('# Debug logging removed for security WebSocket desconectado');
        clearTimeout(wsTimeout);
        setWsConnected(false);
        
        // Tentar reconectar em 3 segundos
        if (isMounted.current && authReady) {
          setTimeout(connectWebSocket, 3000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('# Debug logging removed for security Erro no WebSocket:', error);
        clearTimeout(wsTimeout);
        setWsConnected(false);
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [provedorId, authReady]);

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

  // Polling como backup (mais frequente para reduzir latência)
  useEffect(() => {
    if (!authReady) return;
    
    const interval = setInterval(() => {
      if (isMounted.current) {
        fetchConversations(false); // false = não mostrar loading
      }
    }, 3000); // 3 segundos para maior instantaneidade
    
    return () => clearInterval(interval);
  }, [authReady]);

  // CORREÇÃO: Listener para atualização de permissões do usuário atual
  useEffect(() => {
    const handlePermissionsUpdate = (event) => {
      console.log('Permissões do usuário atualizadas');
      setUserPermissions(event.detail.permissions);
      
      // Recarregar conversas para aplicar as novas permissões
      setTimeout(() => {
        if (isMounted.current) {
          fetchConversations(true);
        }
      }, 500);
    };

    window.addEventListener('userPermissionsUpdated', handlePermissionsUpdate);
    
    return () => {
      window.removeEventListener('userPermissionsUpdated', handlePermissionsUpdate);
    };
  }, []);

  // Definir abas baseado nas permissões
  const getAvailableTabs = () => {
    const activeConversations = conversations.filter(c => {
      const status = c.status || c.additional_attributes?.status;
      const closedStatuses = ['closed', 'encerrada', 'resolved', 'finalizada'];
      return !closedStatuses.includes(status);
    });

    const tabs = [];

    // Abas padrão - Minhas sempre primeiro
    tabs.push({
      id: 'mine',
      label: 'Minhas',
      count: activeConversations.filter(c => {
        const a = c.assignee;
        if (!a || !user) return false;
        return (a.id && a.id === user.id) || (a.username && a.username === user.username);
      }).length,
    });

    // Aba Não atribuídas - conversas em espera (pending) OU com IA (snoozed) OU transferidas
    tabs.push({
      id: 'unassigned',
      label: 'Não atribuídas',
      count: activeConversations.filter(c => {
        const status = c.status || c.additional_attributes?.status;
        const assignedUser = c.additional_attributes?.assigned_user;
        const assignedTeam = c.additional_attributes?.assigned_team;
        
        if (!c.assignee) {
          // Conversas com IA ou em espera geral
          if (status === 'pending' || status === 'snoozed') {
            return true;
          }
          
          // Conversas transferidas para este usuário específico
          if (assignedUser && user && (assignedUser.id === user.id || assignedUser.id === user.id.toString())) {
            return true;
          }
          
          // Conversas transferidas para equipe do usuário
          if (assignedTeam && user && user.team && assignedTeam.id === user.team.id) {
            return true;
          }
        }
        
        return false;
      }).length,
    });

    // Aba Com IA se o usuário tiver a permissão específica - depois de Não atribuídas
    if (userPermissions.includes('view_ai_conversations')) {
      tabs.push({
        id: 'ai',
        label: 'Com IA',
        count: activeConversations.filter(c => {
          const status = c.status || c.additional_attributes?.status;
          return status === 'snoozed' && !c.assignee;
        }).length,
      });
    }

    return tabs;
  };

  const tabs = getAvailableTabs();

  // Filtrar conversas baseado na aba ativa e termo de busca
  const filteredConversations = useMemo(() => {
    let filtered = conversations.filter(c => {
      const status = c.status || c.additional_attributes?.status;
      const closedStatuses = ['closed', 'encerrada', 'resolved', 'finalizada'];
      return !closedStatuses.includes(status);
    });

    // Filtrar por aba
    if (activeTab === 'ai') {
      // Mostrar conversas com IA: status 'snoozed' e não atribuídas
      filtered = filtered.filter(c => {
        const status = c.status || c.additional_attributes?.status;
        return status === 'snoozed' && !c.assignee;
      });
    } else if (activeTab === 'mine') {
      // Mostrar conversas atribuídas ao usuário atual (qualquer status)
      filtered = filtered.filter(c => {
        const a = c.assignee;
        if (!a || !user) return false;
        return (a.id && a.id === user.id) || (a.username && a.username === user.username);
      });
    } else if (activeTab === 'unassigned') {
      // Mostrar conversas não atribuídas em espera (pending) OU com IA (snoozed)
      // OU transferidas para o usuário atual (assigned_user)
      filtered = filtered.filter(c => {
        const status = c.status || c.additional_attributes?.status;
        const assignedUser = c.additional_attributes?.assigned_user;
        const assignedTeam = c.additional_attributes?.assigned_team;
        
        console.log('🔍 DEBUG Não atribuídas:', {
          conversationId: c.id,
          status: status,
          assignee: c.assignee,
          assignedUser: assignedUser,
          assignedTeam: assignedTeam,
          userId: user?.id,
          userTeam: user?.team?.id
        });
        
        // Conversas sem assignee OU transferidas para este usuário/equipe
        if (!c.assignee || (assignedUser && user && (assignedUser.id === user.id || assignedUser.id === user.id.toString()))) {
          // Conversas com IA ou em espera geral
          if (status === 'pending' || status === 'snoozed') {
            return true;
          }
          
          // Conversas transferidas para este usuário específico
          if (assignedUser && user && (assignedUser.id === user.id || assignedUser.id === user.id.toString())) {
            return true;
          }
          
          // Conversas transferidas para equipe do usuário (se ele pertence à equipe)
          if (assignedTeam && user && user.team && assignedTeam.id === user.team.id) {
            return true;
          }
        }
        
        return false;
      });
    }

    // Filtrar por termo de busca
    if (searchTerm && searchTerm.trim().length >= 2) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(c => {
        const contactName = c.contact?.name || '';
        const lastMessage = c.last_message?.content || '';
        const phone = c.contact?.phone || '';
        
        return contactName.toLowerCase().includes(searchLower) ||
               lastMessage.toLowerCase().includes(searchLower) ||
               phone.includes(searchTerm);
      });
    }

    return filtered;
  }, [conversations, activeTab, searchTerm, user?.id, userPermissions]);

  return (
    <div className="w-80 border-r border-border bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Conversas</h2>
          <div className="flex items-center space-x-2">
            {/* Status de conexão */}
            <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
              wsConnected 
                ? 'bg-green-100 text-green-800' 
                : authReady 
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                wsConnected ? 'bg-green-500' : authReady ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <span>
                {wsConnected ? 'Online' : authReady ? 'Conectando...' : 'Offline'}
              </span>
            </div>
            {/* Botão de ativar sons removido */}
            
            {/* Notificação de nova mensagem */}
            {newMessageNotification && (
              <div className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs animate-pulse">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>Nova mensagem!</span>
              </div>
            )}
            
            <button 
              onClick={() => fetchConversations(true)}
              className="text-muted-foreground hover:text-foreground p-1"
              title="Atualizar conversas"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <div className="relative">
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('# Debug logging removed for security Clicou nos 3 pontinhos da página Atendimento');
                  setShowMenuAtendimento(!showMenuAtendimento);
                }}
                className="text-muted-foreground hover:text-foreground p-1"
                title="Novo atendimento"
              >
                <MoreHorizontal size={20} />
              </button>
              
              {/* Menu de opções */}
              {showMenuAtendimento && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-card border border-border rounded-lg shadow-lg py-1 z-50">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenuAtendimento(false);
                      setModalNovoContato(true);
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent flex items-center space-x-2"
                  >
                    <User className="w-4 h-4" />
                    <span>Novo Contato</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenuAtendimento(false);
                      setModalContatoExistente(true);
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-accent flex items-center space-x-2"
                  >
                    <Search className="w-4 h-4" />
                    <span>Contato Existente</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Pesquisar mensagens em conversas"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="niochat-input pl-8 w-full text-sm"
          />
          {searchTerm && (
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setSearchTerm('')}
            >
              Limpar
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-muted rounded-lg p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-2 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-1 bg-primary text-primary-foreground text-xs px-1 py-0.5 rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {!authReady ? (
          <div className="p-3 text-center text-muted-foreground">
            {!hasInitialized ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <span>Verificando autenticação...</span>
              </div>
            ) : (
              <div>
                <div className="mb-3">
                  <svg className="w-12 h-12 mx-auto text-muted-foreground mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <h3 className="text-lg font-medium mb-2">Acesso Restrito</h3>
                  <p className="text-sm mb-4">Você precisa estar logado para acessar as conversas.</p>
                </div>
                <button 
                  onClick={() => window.location.href = '/admin/login/'}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                >
                  Fazer Login
                </button>
                <p className="text-xs mt-2 text-muted-foreground">
                  Ou acesse o painel administrativo para autenticação
                </p>
              </div>
            )}
          </div>
        ) : !hasInitialized ? (
          <div className="p-3 text-center text-muted-foreground">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              <span>Carregando...</span>
            </div>
            <p className="text-xs mt-2">Buscando conversas...</p>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-3 text-center text-muted-foreground">
            {conversations.length === 0 ? (
              <div>
                <p>Nenhuma conversa encontrada.</p>
                <p className="text-xs mt-1">Aguardando conversas ativas...</p>
                <button 
                  onClick={() => fetchConversations(true)}
                  className="mt-2 px-3 py-1 bg-primary text-primary-foreground text-xs rounded hover:bg-primary/90"
                >
                  Tentar novamente
                </button>
              </div>
            ) : (
              <div>
                <p>Nenhuma conversa na aba "{tabs.find(t => t.id === activeTab)?.label}".</p>
                <p className="text-xs mt-1">Total: {conversations.length}</p>
              </div>
            )}
          </div>
        ) : (
          filteredConversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => onConversationSelect(conversation)}
              className={`p-3 border-b border-border cursor-pointer transition-colors hover:bg-muted/50 ${
                selectedConversation?.id === conversation.id ? 'bg-muted' : ''
              }`}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                    {conversation.contact?.avatar ? (
                      <img
                        src={conversation.contact.avatar}
                        alt={conversation.contact.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <User size={20} className="text-primary" />
                    )}
                  </div>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-foreground truncate">
                      {conversation.contact?.name || 'Contato sem nome'}
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      {conversation.last_message?.created_at ? 
                        new Date(conversation.last_message.created_at).toLocaleTimeString('pt-BR', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        }) : ''
                      }
                    </span>
                  </div>
                  
                  <p className="text-sm text-muted-foreground truncate mt-1">
                    {conversation.last_message?.content || 'Nenhuma mensagem'}
                  </p>
                  
                  {/* # Debug logging removed for security Tempo de atendimento em aberto */}
                  <div className="mt-2">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-600 text-white">
                      <Clock size={12} className="mr-1" />
                      Há {(() => {
                        const agora = new Date();
                        const inicio = new Date(conversation.created_at);
                        const diffMs = agora - inicio;
                        const diffMinutos = Math.floor(diffMs / (1000 * 60));
                        const diffHoras = Math.floor(diffMinutos / 60);
                        const diffDias = Math.floor(diffHoras / 24);
                        
                        if (diffDias > 0) {
                          return `${diffDias} dia${diffDias > 1 ? 's' : ''}`;
                        } else if (diffHoras > 0) {
                          return `${diffHoras}h ${diffMinutos % 60}min`;
                        } else {
                          return `${diffMinutos} min`;
                        }
                      })()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* # Debug logging removed for security Modal de novo contato */}
      <Dialog open={modalNovoContato} onOpenChange={setModalNovoContato}>
        <DialogContent className="max-w-md w-full">
          <DialogHeader>
            <DialogTitle>Novo Contato</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Nome do Contato</label>
              <input
                type="text"
                value={novoContato.nome}
                onChange={(e) => setNovoContato(prev => ({ ...prev, nome: e.target.value }))}
                placeholder="Digite o nome do contato"
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Telefone (com 55)</label>
              <input
                type="text"
                value={novoContato.telefone}
                onChange={(e) => setNovoContato(prev => ({ ...prev, telefone: e.target.value }))}
                placeholder="5511999999999"
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Canal</label>
              <select
                value={novoContato.canal}
                onChange={(e) => setNovoContato(prev => ({ ...prev, canal: e.target.value }))}
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="whatsapp">WhatsApp</option>
                <option value="telegram">Telegram</option>
                <option value="email">Email</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Mensagem</label>
              <textarea
                value={novoContato.mensagem}
                onChange={(e) => setNovoContato(prev => ({ ...prev, mensagem: e.target.value }))}
                placeholder="Digite a mensagem a ser enviada"
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
            </div>
            
            <div className="flex items-center justify-end space-x-2 pt-4">
              <button
                onClick={() => setModalNovoContato(false)}
                className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                disabled={enviandoAtendimento}
              >
                Cancelar
              </button>
              <button
                onClick={handleNovoContato}
                disabled={enviandoAtendimento}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {enviandoAtendimento ? 'Enviando...' : 'Enviar Mensagem'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* # Debug logging removed for security Modal de contato existente */}
      <Dialog open={modalContatoExistente} onOpenChange={setModalContatoExistente}>
        <DialogContent className="max-w-md w-full">
          <DialogHeader>
            <DialogTitle>Contato Existente</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Buscar Contato</label>
              <input
                type="text"
                value={contatoExistente.busca}
                onChange={(e) => {
                  setContatoExistente(prev => ({ ...prev, busca: e.target.value }));
                  buscarContatos(e.target.value);
                }}
                placeholder="Digite nome ou telefone"
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            
            {/* Lista de contatos encontrados */}
            {contatosEncontrados.length > 0 && (
              <div className="max-h-40 overflow-y-auto border border-border rounded-lg">
                {contatosEncontrados.map(contato => (
                  <button
                    key={contato.id}
                    onClick={() => setContatoExistente(prev => ({ ...prev, contato }))}
                    className={`w-full text-left p-3 hover:bg-accent transition-colors border-b last:border-b-0 ${
                      contatoExistente.contato?.id === contato.id ? 'bg-accent' : ''
                    }`}
                  >
                    <div className="font-medium">{contato.name}</div>
                    <div className="text-sm text-muted-foreground">{contato.phone}</div>
                  </button>
                ))}
              </div>
            )}
            
            {/* Contato selecionado */}
            {contatoExistente.contato && (
              <div className="p-3 bg-muted rounded-lg">
                <div className="font-medium">Contato Selecionado:</div>
                <div className="text-sm">{contatoExistente.contato.name} - {contatoExistente.contato.phone}</div>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium mb-2">Mensagem</label>
              <textarea
                value={contatoExistente.mensagem}
                onChange={(e) => setContatoExistente(prev => ({ ...prev, mensagem: e.target.value }))}
                placeholder="Digite a mensagem a ser enviada"
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
            </div>
            
            <div className="flex items-center justify-end space-x-2 pt-4">
              <button
                onClick={() => {
                  setModalContatoExistente(false);
                  setContatoExistente({ busca: '', contato: null, mensagem: '' });
                  setContatosEncontrados([]);
                }}
                className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
                disabled={enviandoAtendimento}
              >
                Cancelar
              </button>
              <button
                onClick={handleContatoExistente}
                disabled={enviandoAtendimento || !contatoExistente.contato}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {enviandoAtendimento ? 'Enviando...' : 'Enviar Mensagem'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ConversationList;