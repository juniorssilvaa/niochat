import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { APP_VERSION } from '../config/version';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // 1. Autentica e pega o token
      const res = await axios.post('/api-token-auth/', { username, password });
      const token = res.data.token;

      // Salva o token no localStorage
      localStorage.setItem('token', token);
      
      // 🔥 CONFIGURAÇÃO IMPORTANTE: Define o token como padrão para todas as requisições
      axios.defaults.headers.common['Authorization'] = `Token ${token}`;

      // 2. Busca dados do usuário logado
      const userRes = await axios.get('/auth/me/');
      const userData = userRes.data;

      // 3. Atualiza estado da aplicação
      onLogin({ ...userData, token });
      
      setLoading(false);

      // 4. Pequeno delay para garantir que tudo está configurado
      setTimeout(() => {
        // Redireciona para o painel do provedor
        if (userData.user_type === 'superadmin') {
          navigate('/superadmin', { replace: true });
        } else if (userData.provedor_id) {
          if (userData.user_type === 'agent') {
            navigate(`/app/accounts/${userData.provedor_id}/conversations`, { replace: true });
          } else {
            navigate(`/app/accounts/${userData.provedor_id}/dashboard`, { replace: true });
          }
        } else {
          navigate('/dashboard', { replace: true });
        }
        
        // 🔥 FORÇA UM RELOAD PARA INICIALIZAR TODOS OS COMPONENTES
        window.location.reload();
      }, 100);

    } catch (err) {
      setLoading(false);
      console.error('Erro no login:', err);
      
      // Limpa token inválido
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      
      setError('Usuário ou senha inválidos');
    }
  };

  // O restante do componente permanece igual
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#1a1f2e' }}>
      <div className="rounded-lg shadow-lg flex flex-col md:flex-row w-full max-w-3xl border" 
           style={{ backgroundColor: '#252b3d', borderColor: '#374151' }}>
        {/* Logo */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 border-b md:border-b-0 md:border-r" 
             style={{ borderColor: '#374151' }}>
          <img src="/logo.png" alt="Logo" className="w-48 mb-8" />
        </div>
        {/* Formulário */}
        <div className="flex-1 flex flex-col justify-center p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-bold mb-2" style={{ color: '#e2e8f0' }}>Usuário</label>
              <input
                type="text"
                className="w-full px-4 py-2 rounded focus:outline-none border transition-colors"
                style={{ 
                  backgroundColor: '#374151', 
                  color: '#e2e8f0', 
                  borderColor: '#374151'
                }}
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div>
              <label className="block text-sm font-bold mb-2" style={{ color: '#e2e8f0' }}>Senha</label>
              <input
                type="password"
                className="w-full px-4 py-2 rounded focus:outline-none border transition-colors"
                style={{ 
                  backgroundColor: '#374151', 
                  color: '#e2e8f0', 
                  borderColor: '#374151'
                }}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <div className="text-sm" style={{ color: '#ef4444' }}>{error}</div>}
            <button
              type="submit"
              className="w-full py-2 rounded font-bold transition-colors"
              style={{ 
                backgroundColor: '#3b82f6', 
                color: '#ffffff'
              }}
              disabled={loading}
            >
              {loading ? 'Acessando...' : 'Acessar'}
            </button>
          </form>
          <div className="text-center text-xs mt-8" style={{ color: '#9ca3af' }}>Versão {APP_VERSION}</div>
        </div>
      </div>
    </div>
  );
}
