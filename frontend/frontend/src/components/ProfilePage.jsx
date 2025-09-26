import React, { useState, useEffect, useRef } from 'react';
import { User, Shield, Bell, Volume2, Save, Key, Settings } from 'lucide-react';
import axios from 'axios';
import useSessionTimeout from '../hooks/useSessionTimeout';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [userData, setUserData] = useState(null);
  const audioRef = useRef(null);
  const { updateTimeout } = useSessionTimeout();
  // Sons disponíveis - carregados dinamicamente
  const [availableSounds, setAvailableSounds] = useState([]);
  const [messageSounds, setMessageSounds] = useState([]);
  const [conversationSounds, setConversationSounds] = useState([]);
  const [settings, setSettings] = useState({
    profile: {
      name: '',
      email: '',
      phone: '',
      avatar: null
    },
    notifications: {
      soundNotifications: false,
      newMessageSound: 'message_in_01.mp3',
      newConversationSound: 'chat_new_01.mp3'
    },
    security: {
      twoFactorAuth: false,
      sessionTimeout: 30
    }
  });

  // Carregar sons disponíveis
  useEffect(() => {
    const loadAvailableSounds = async () => {
      try {
        // Lista de sons disponíveis baseada nos arquivos na pasta /sounds
        const allSounds = [
          'message_in_01.mp3',
          'message_in_02.mp3',
          'message_in_03.mp3',
          'message_in_04.mp3',
          'message_in_05.mp3',
          'message_in_06.mp3',
          'message_in_07.mp3',
          'message_in_08.mp3',
          'message_in_09.mp3',
          'message_in_010.mp3',
          'message_in_011.mp3',
          'chat_new_01.mp3',
          'chat_new_02.mp3',
          'chat_new_03.mp3',
          'chat_new_04.mp3',
          'chat_new_05.mp3',
          'chat_new_06.mp3',
          'chat_new_07.mp3',
          'chat_new_08.mp3',
          'chat_new_09.mp3',
          'chat_new_010.mp3',
          'chat_new_011.mp3'
        ];
        
        // Filtrar sons por categoria
        const messageSoundsList = allSounds.filter(sound => sound.startsWith('message_in_'));
        const conversationSoundsList = allSounds.filter(sound => sound.startsWith('chat_new_'));
        
        setAvailableSounds(allSounds);
        setMessageSounds(messageSoundsList);
        setConversationSounds(conversationSoundsList);
      } catch (error) {
        console.error('Erro ao carregar sons:', error);
      }
    };
    
    loadAvailableSounds();
  }, []);

  // Buscar dados do usuário
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/auth/me/', {
          headers: { Authorization: `Token ${token}` }
        });
        
        const user = response.data;
        setUserData(user);
        const storedSoundEnabled = localStorage.getItem('sound_notifications_enabled');
        const storedMsgSound = localStorage.getItem('sound_new_message');
        const storedConvSound = localStorage.getItem('sound_new_conversation');
        setSettings({
          ...settings,
          profile: {
            name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username,
            email: user.email || '',
            phone: user.phone || '',
            avatar: user.avatar
          },
          notifications: {
            ...settings.notifications,
            soundNotifications: typeof user.sound_notifications_enabled === 'boolean' 
              ? user.sound_notifications_enabled 
              : (storedSoundEnabled ? storedSoundEnabled === 'true' : settings.notifications.soundNotifications),
            newMessageSound: user.new_message_sound || storedMsgSound || settings.notifications.newMessageSound,
            newConversationSound: user.new_conversation_sound || storedConvSound || settings.notifications.newConversationSound
          },
          security: {
            ...settings.security,
            sessionTimeout: user.session_timeout || settings.security.sessionTimeout
          }
        });
      } catch (error) {
        console.error('Erro ao buscar dados do usuário:', error);
      }
    };

    fetchUserData();
  }, []);

  const handleSaveProfile = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const token = localStorage.getItem('token');
      const [firstName, ...lastNameParts] = settings.profile.name.split(' ');
      const lastName = lastNameParts.join(' ') || '';
      
      await axios.patch('/api/auth/me/', {
        first_name: firstName,
        last_name: lastName,
        email: settings.profile.email,
        phone: settings.profile.phone,
        session_timeout: settings.security.sessionTimeout
      }, {
        headers: { Authorization: `Token ${token}` }
      });
      
      // Atualizar timeout da sessão
      try {
        await axios.patch('/api/auth/me/', {
          session_timeout: settings.security.sessionTimeout
        }, {
          headers: { Authorization: `Token ${token}` }
        });
        
        // Atualizar o timeout no frontend
        await updateTimeout();
      } catch (error) {
        console.error('Erro ao atualizar timeout da sessão:', error);
      }
      
      setMessage('Perfil atualizado com sucesso!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Erro ao atualizar perfil:', error);
      setMessage('Erro ao atualizar perfil. Tente novamente.');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const formatSoundLabel = (fileName) => {
    // Remover extensão e prefixos, formatar nome
    let base = fileName.replace(/\.(mp3|wav)$/i, '');
    
    // Remover prefixos específicos
    base = base.replace(/^(message_in_|chat_new_)/, '');
    
    // Converter para formato legível
    base = base.replace(/_/g, ' ');
    
    // Capitalizar primeira letra
    return base.charAt(0).toUpperCase() + base.slice(1);
  };

  const handleToggleSoundNotifications = async (checked) => {
    setSettings({
      ...settings,
      notifications: { ...settings.notifications, soundNotifications: checked }
    });
    localStorage.setItem('sound_notifications_enabled', String(checked));
    try {
      const token = localStorage.getItem('token');
      await axios.patch('/api/auth/me/', {
        sound_notifications_enabled: checked
      }, {
        headers: { Authorization: `Token ${token}` }
      });
      // Desbloquear autoplay imediatamente quando o usuário habilitar
      if (checked) {
        try {
          const src = `/sounds/${settings.notifications.newMessageSound}`;
          if (!audioRef.current) {
            audioRef.current = new Audio(src);
          } else {
            audioRef.current.src = src;
          }
          audioRef.current.currentTime = 0;
          await audioRef.current.play().catch(() => {});
        } catch (_) {}
      }
    } catch (e) {
      console.error('Erro ao salvar preferência de som no servidor:', e);
    }
  };

  const handleSelectSound = async (type, value) => {
    setSettings({
      ...settings,
      notifications: { ...settings.notifications, [type]: value }
    });
    if (type === 'newMessageSound') {
      localStorage.setItem('sound_new_message', value);
    }
    if (type === 'newConversationSound') {
      localStorage.setItem('sound_new_conversation', value);
    }
    try {
      const token = localStorage.getItem('token');
      await axios.patch('/api/auth/me/', {
        [type === 'newMessageSound' ? 'new_message_sound' : 'new_conversation_sound']: value
      }, {
        headers: { Authorization: `Token ${token}` }
      });
    } catch (e) {
      console.error('Erro ao salvar som no servidor:', e);
    }
  };

  const handlePreviewSound = (fileName) => {
    try {
      const src = `/sounds/${fileName}`;
      if (!audioRef.current) {
        audioRef.current = new Audio(src);
      } else {
        audioRef.current.pause();
        audioRef.current.src = src;
      }
      audioRef.current.currentTime = 0;
      audioRef.current.play();
    } catch (e) {
      console.error('Erro ao reproduzir som:', e);
    }
  };

  const handleResetPassword = async () => {
    const newPassword = prompt('Digite sua nova senha:');
    if (!newPassword) return;
    
    const confirmPassword = prompt('Confirme sua nova senha:');
    if (newPassword !== confirmPassword) {
      alert('As senhas não coincidem!');
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/users/reset-password/', {
        new_password: newPassword
      }, {
        headers: { Authorization: `Token ${token}` }
      });
      
      setMessage('Senha alterada com sucesso!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Erro ao alterar senha:', error);
      setMessage('Erro ao alterar senha. Tente novamente.');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Perfil', icon: User },
    { id: 'notifications', label: 'Notificações', icon: Bell },
    { id: 'security', label: 'Segurança', icon: Shield }
  ];

  const renderProfileSettings = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-card-foreground">
          Informações Pessoais
        </h3>
        <button
          onClick={handleSaveProfile}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          {loading ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Nome Completo
          </label>
          <input
            type="text"
            value={settings.profile.name}
            onChange={(e) => setSettings({
              ...settings,
              profile: { ...settings.profile, name: e.target.value }
            })}
            className="niochat-input"
            placeholder="Digite seu nome completo"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            E-mail
          </label>
          <input
            type="email"
            value={settings.profile.email}
            onChange={(e) => setSettings({
              ...settings,
              profile: { ...settings.profile, email: e.target.value }
            })}
            className="niochat-input"
            placeholder="Digite seu e-mail"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Telefone
          </label>
          <input
            type="tel"
            value={settings.profile.phone}
            onChange={(e) => setSettings({
              ...settings,
              profile: { ...settings.profile, phone: e.target.value }
            })}
            className="niochat-input"
            placeholder="Digite seu telefone"
          />
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-card-foreground mb-4">
        Preferências de Notificação
      </h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 border border-border rounded-lg">
          <div className="flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-muted-foreground" />
            <h4 className="font-medium text-card-foreground">Notificações Sonoras</h4>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.notifications.soundNotifications}
              onChange={(e) => handleToggleSoundNotifications(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>
      </div>
      {settings.notifications.soundNotifications && (
        <div className="space-y-4">
          <div className="p-4 border border-border rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-card-foreground mb-2">
                  Som para novas mensagens
                </label>
                <select
                  value={settings.notifications.newMessageSound}
                  onChange={(e) => handleSelectSound('newMessageSound', e.target.value)}
                  className="niochat-input"
                >
                  {messageSounds.length > 0 ? messageSounds.map((s) => (
                    <option key={s} value={s}>{formatSoundLabel(s)}</option>
                  )) : (
                    <option value="">Carregando sons...</option>
                  )}
                </select>
              </div>
              <div>
                <button
                  type="button"
                  onClick={() => handlePreviewSound(settings.notifications.newMessageSound)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                >
                  Reproduzir
                </button>
              </div>
            </div>
          </div>
          <div className="p-4 border border-border rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-card-foreground mb-2">
                  Som para novas conversas
                </label>
                <select
                  value={settings.notifications.newConversationSound}
                  onChange={(e) => handleSelectSound('newConversationSound', e.target.value)}
                  className="niochat-input"
                >
                  {conversationSounds.length > 0 ? conversationSounds.map((s) => (
                    <option key={s} value={s}>{formatSoundLabel(s)}</option>
                  )) : (
                    <option value="">Carregando sons...</option>
                  )}
                </select>
              </div>
              <div>
                <button
                  type="button"
                  onClick={() => handlePreviewSound(settings.notifications.newConversationSound)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                >
                  Reproduzir
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-card-foreground mb-4">
        Configurações de Segurança
      </h3>
      <div className="space-y-4">
        <div className="p-4 border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-card-foreground">Autenticação de Dois Fatores</h4>
              <p className="text-sm text-muted-foreground">
                Adicione uma camada extra de segurança à sua conta
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.security.twoFactorAuth}
                onChange={(e) => setSettings({
                  ...settings,
                  security: { ...settings.security, twoFactorAuth: e.target.checked }
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-muted peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
            </label>
          </div>
        </div>

        <div className="p-4 border border-border rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-card-foreground">Redefinir Senha</h4>
              <p className="text-sm text-muted-foreground">
                Altere sua senha de acesso ao sistema
              </p>
            </div>
            <button
              onClick={handleResetPassword}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Key className="w-4 h-4" />
              {loading ? 'Alterando...' : 'Alterar Senha'}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-card-foreground mb-2">
            Timeout da Sessão (minutos)
          </label>
          <div className="flex gap-2">
            <select
              value={settings.security.sessionTimeout}
              onChange={(e) => setSettings({
                ...settings,
                security: { ...settings.security, sessionTimeout: parseInt(e.target.value) }
              })}
              className="niochat-input flex-1"
            >
              <option value={1}>1 minuto</option>
              <option value={2}>2 minutos</option>
              <option value={15}>15 minutos</option>
              <option value={30}>30 minutos</option>
              <option value={60}>1 hora</option>
              <option value={120}>2 horas</option>
            </select>
            <button
              onClick={handleSaveProfile}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {loading ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileSettings();
      case 'notifications':
        return renderNotificationSettings();
      case 'security':
        return renderSecuritySettings();
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 p-6 bg-background overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-foreground mb-6 flex items-center gap-3">
          <User className="w-8 h-8 text-muted-foreground" /> Perfil
        </h1>
        
        {/* Mensagem de feedback global */}
        {message && (
          <div className={`mb-4 p-4 rounded-lg border ${
            message.includes('sucesso') 
              ? 'bg-green-50 text-green-800 border-green-200' 
              : 'bg-red-50 text-red-800 border-red-200'
          }`}>
            <div className="flex items-center gap-2">
              {message.includes('sucesso') ? (
                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
              <span className="font-medium">{message}</span>
            </div>
          </div>
        )}
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <div className="lg:w-64">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="niochat-card p-6">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 