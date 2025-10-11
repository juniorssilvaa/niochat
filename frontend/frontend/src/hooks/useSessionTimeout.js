import { useEffect, useRef } from 'react';
import axios from 'axios';

const useSessionTimeout = () => {
  // Verificar se estamos em um ambiente React válido
  if (typeof window === 'undefined') {
    return { startTimeout: () => {}, updateTimeout: () => {} };
  }

  const timeoutRef = useRef(null);
  const warningTimeoutRef = useRef(null);
  const sessionTimeoutRef = useRef(30); // valor padrão de 30 minutos

  // Buscar timeout configurado do usuário
  const fetchUserSessionTimeout = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const response = await axios.get('/api/auth/me/', {
          headers: { Authorization: `Token ${token}` }
        });
        const userSessionTimeout = response.data.session_timeout || 30;
        sessionTimeoutRef.current = userSessionTimeout;
        return userSessionTimeout;
      }
    } catch (error) {
      console.error('Erro ao buscar timeout da sessão:', error);
    }
    return 30; // valor padrão
  };

  const resetTimeout = () => {
    // Limpar timeouts anteriores
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
    }

    const timeoutMinutes = sessionTimeoutRef.current;
    const timeoutMs = timeoutMinutes * 60 * 1000;

    // Definir novo timeout para logout automático
    timeoutRef.current = setTimeout(() => {
      // Fazer logout automático
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      alert('Sua sessão expirou por inatividade. Você será redirecionado para a página de login.');
      window.location.href = '/login';
      window.location.reload();
    }, timeoutMs);

    // Definir timeout de aviso (30 segundos antes do logout para timeouts maiores que 1 minuto)
    if (timeoutMinutes > 1) {
      const warningTime = timeoutMs - 30000; // 30 segundos antes
      warningTimeoutRef.current = setTimeout(() => {
        // Mostrar aviso de timeout
        alert(`Sua sessão expirará em 30 segundos por inatividade. Realize alguma ação para continuar.`);
      }, warningTime);
    } else if (timeoutMinutes === 1) {
      // Para timeout de 1 minuto, mostrar aviso após 30 segundos
      warningTimeoutRef.current = setTimeout(() => {
        // Mostrar aviso de timeout
        alert(`Sua sessão expirará em 30 segundos por inatividade. Realize alguma ação para continuar.`);
      }, 30 * 1000);
    }
  };

  const startTimeout = () => {
    // Buscar timeout configurado do usuário e iniciar o timeout
    fetchUserSessionTimeout().then(() => {
      resetTimeout();

      // Resetar timeout em qualquer atividade do usuário
      const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click', 'keydown'];
      events.forEach(event => {
        document.addEventListener(event, resetTimeout, true);
      });

      // Retornar função de limpeza
      return () => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        if (warningTimeoutRef.current) {
          clearTimeout(warningTimeoutRef.current);
        }
        events.forEach(event => {
          document.removeEventListener(event, resetTimeout, true);
        });
      };
    });
  };

  // Função para atualizar o timeout quando as configurações mudarem
  const updateTimeout = async () => {
    await fetchUserSessionTimeout();
    resetTimeout();
  };

  return { startTimeout, updateTimeout };
};

export default useSessionTimeout;