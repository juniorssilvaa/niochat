import React, { useEffect, useState } from 'react';
import { Eye, Search, Filter, Calendar, X, MessageSquare, Clock, Hash, Bot, User } from 'lucide-react';
import axios from 'axios';

// Importar ícones dos canais
import whatsappIcon from '../assets/whatsapp.png';
import telegramIcon from '../assets/telegram.png';
import gmailIcon from '../assets/gmail.png';

export default function ConversationAudit({ provedorId }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversationDetails, setConversationDetails] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: ''
  });

  useEffect(() => {
    if (provedorId) {
      fetchConversations();
      fetchStats();
    }
  }, [provedorId]);

  const fetchConversations = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        provedor_id: provedorId,
        conversation_closed: 'true',
        page_size: 50
      });

      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);

      const response = await axios.get(`/api/audit-logs/?${params}`, {
        headers: { Authorization: `Token ${token}` }
      });

      const data = response.data.results || response.data || [];
      setConversations(data);
    } catch (err) {
      console.error('Erro ao buscar conversas:', err);
      setError('Erro ao carregar conversas encerradas');
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/audit-logs/conversation_stats/?provedor_id=${provedorId}`, {
        headers: { Authorization: `Token ${token}` }
      });
      setStats(response.data);
    } catch (err) {
      console.error('Erro ao buscar estatísticas:', err);
    }
  };

  const fetchConversationDetails = async (conversationId) => {
    setLoadingDetails(true);
    setLoadingMessages(true);
    try {
      const token = localStorage.getItem('token');
      
      // Buscar detalhes da conversa
      const detailsResponse = await axios.get(`/api/conversations/${conversationId}/`, {
        headers: { Authorization: `Token ${token}` }
      });
      let conversationData = detailsResponse.data;
      
      // Buscar CSAT rating do AuditLog
      const auditResponse = await axios.get(`/api/audit-logs/?conversation_closed=true&page_size=50`, {
        headers: { Authorization: `Token ${token}` }
      });
      
      const auditLogs = auditResponse.data.results || auditResponse.data || [];
      const conversationAudit = auditLogs.find(log => 
        log.conversation_id === conversationId && log.csat_rating !== null
      );
      
      // Adicionar CSAT rating aos dados da conversa
      if (conversationAudit) {
        conversationData.csat_rating = conversationAudit.csat_rating;
      }
      
      setConversationDetails(conversationData);
      
      // Buscar mensagens da conversa
      const messagesResponse = await axios.get(`/api/messages/?conversation=${conversationId}`, {
        headers: { Authorization: `Token ${token}` }
      });
      setConversationMessages(messagesResponse.data.results || messagesResponse.data || []);
      
    } catch (err) {
      console.error('Erro ao buscar detalhes da conversa:', err);
      setConversationDetails(null);
      setConversationMessages([]);
    } finally {
      setLoadingDetails(false);
      setLoadingMessages(false);
    }
  };

  const openConversationModal = (conversationId) => {
    setSelectedConversation(conversationId);
    fetchConversationDetails(conversationId);
  };

  const closeConversationModal = () => {
    setSelectedConversation(null);
    setConversationDetails(null);
    setConversationMessages([]);
  };

  const getChannelIcon = (channelType) => {
    switch (channelType) {
      case 'whatsapp':
        return <img src={whatsappIcon} alt="WhatsApp" className="w-4 h-4" />;
      case 'telegram':
        return <img src={telegramIcon} alt="Telegram" className="w-4 h-4" />;
      case 'email':
        return <img src={gmailIcon} alt="Email" className="w-4 h-4" />;
      default:
        return <img src={whatsappIcon} alt="WhatsApp" className="w-4 h-4" />;
    }
  };

  const getActionBadge = (action) => {
    if (action === 'conversation_closed_ai') {
      return 'bg-purple-100 text-purple-800';
    }
    return 'bg-blue-100 text-blue-800';
  };

  const getActionIcon = (action) => {
    if (action === 'conversation_closed_ai') {
      return <Bot className="w-4 h-4 text-purple-600" />;
    }
    return <User className="w-4 h-4 text-blue-600" />;
  };

  const formatDuration = (duration) => {
    if (!duration) return '-';
    if (typeof duration === 'string' && duration.includes('min')) {
      return duration;
    }
    return duration;
  };

  const filteredConversations = conversations.filter(conv => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      (conv.contact_name && conv.contact_name.toLowerCase().includes(searchLower)) ||
      (conv.user && conv.user.toLowerCase().includes(searchLower))
    );
  });

  const getCSATEmoji = (csatRating) => {
    // Mapear rating CSAT para emoji
    const emojiMap = {
      1: '😡',
      2: '😕', 
      3: '😐',
      4: '🙂',
      5: '🤩'
    };
    return emojiMap[csatRating] || '-';
  };

  if (!provedorId) {
    return (
      <div className="flex-1 p-6 bg-background">
        <div className="text-center text-muted-foreground">
          ID do provedor não fornecido
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 bg-background overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground mb-2">Auditoria do Sistema</h1>
          <p className="text-muted-foreground">
            Veja todas as conversas encerradas no sistema, incluindo quem as encerrou e detalhes.
          </p>
        </div>

        {/* Estatísticas */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-card p-6 rounded-lg border">
              <div className="text-2xl font-bold text-foreground mb-1">
                {stats.total_closed || 0}
              </div>
              <div className="text-sm text-muted-foreground">Total Encerradas</div>
            </div>
            <div className="bg-card p-6 rounded-lg border">
              <div className="text-2xl font-bold text-blue-600 mb-1">
                {stats.closed_by_agent || 0}
              </div>
              <div className="text-sm text-muted-foreground">Por Agentes</div>
            </div>
            <div className="bg-card p-6 rounded-lg border">
              <div className="text-2xl font-bold text-purple-600 mb-1">
                {stats.closed_by_ai || 0}
              </div>
              <div className="text-sm text-muted-foreground">Por IA</div>
            </div>
            <div className="bg-card p-6 rounded-lg border">
              <div className="text-2xl font-bold text-green-600 mb-1">
                {stats.percentage_ai_resolved ? `${stats.percentage_ai_resolved.toFixed(0)}%` : '0%'}
              </div>
              <div className="text-sm text-muted-foreground">Taxa IA</div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-card p-4 rounded-lg border mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Pesquisar por cliente ou agente..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                className="px-3 py-2 border rounded-lg bg-background"
              />
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                className="px-3 py-2 border rounded-lg bg-background"
              />
              <button
                onClick={fetchConversations}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Filtrar
              </button>
            </div>
          </div>
        </div>

        {/* Tabela */}
        <div className="bg-card rounded-lg border overflow-hidden">
          {loading && (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-muted-foreground">Carregando conversas...</p>
            </div>
          )}

          {error && (
            <div className="p-8 text-center text-red-500">
              {error}
            </div>
          )}

          {!loading && !error && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Cliente</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Agente</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Data/Hora</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Canais</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Detalhes</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Duração</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredConversations.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                        <MessageSquare className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                        <p className="text-lg font-medium">Nenhuma conversa encerrada encontrada</p>
                        <p className="text-sm">As conversas encerradas aparecerão aqui quando houver atividades.</p>
                      </td>
                    </tr>
                  )}
                  
                  {filteredConversations.map((conv) => (
                    <tr 
                      key={conv.id} 
                      className="hover:bg-muted/50 cursor-pointer transition-colors"
                      onClick={() => openConversationModal(conv.conversation_id)}
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">
                          {conv.contact_name || 'Cliente'}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Conversa #{conv.conversation_id}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getActionIcon(conv.action)}
                          <div className="font-medium">
                            {conv.action === 'conversation_closed_ai' ? 'Sistema IA' : 
                             (typeof conv.user === 'string' ? conv.user.split(' (')[0] : conv.user || 'Sistema')}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm">
                          {new Date(conv.timestamp).toLocaleDateString('pt-BR')}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {new Date(conv.timestamp).toLocaleTimeString('pt-BR')}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getChannelIcon(conv.channel_type)}
                          <span className="text-sm capitalize">
                            {conv.channel_type === 'whatsapp' ? 'WhatsApp' :
                             conv.channel_type === 'telegram' ? 'Telegram' :
                             conv.channel_type === 'email' ? 'Email' :
                             conv.channel_type || 'WhatsApp'}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm">
                          {conv.message_count || 0} mensagens
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Avaliação: <span className="text-lg">{getCSATEmoji(conv.csat_rating)}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {conv.resolution_type === 'ai_resolved' ? 'IA resolveu automaticamente' :
                           conv.resolution_type === 'problem_solved' ? 'Problema resolvido com sucesso' :
                           conv.resolution_type === 'client_ended' ? 'Cliente encerrou a conversa' :
                           conv.resolution_type === 'finalized_after_confirmation' ? 'Finalizado pela IA após confirmação do cliente' :
                           'Conversa finalizada'}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium">
                          {formatDuration(conv.conversation_duration_formatted) || '10 min'}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal de Detalhes */}
        {selectedConversation && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-background rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header do Modal */}
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Detalhes da Conversa #conv-{selectedConversation.toString().padStart(3, '0')}
                </h2>
                <button
                  onClick={closeConversationModal}
                  className="p-2 hover:bg-muted rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Conteúdo do Modal */}
              <div className="p-6">
                {loadingDetails ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-muted-foreground">Carregando detalhes...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Informações Básicas */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Cliente</div>
                        <div className="font-medium">
                          {conversationDetails?.contact?.name || 'Cliente'}
                        </div>
                      </div>
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Agente</div>
                        <div className="flex items-center gap-2">
                          {conversationDetails?.assignee ? (
                            <>
                              <User className="w-4 h-4 text-blue-600" />
                              <span className="font-medium">
                                {conversationDetails.assignee.first_name} {conversationDetails.assignee.last_name}
                              </span>
                            </>
                          ) : (
                            <>
                              <Bot className="w-4 h-4 text-purple-600" />
                              <span className="font-medium">Sistema IA</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Duração</div>
                        <div className="font-medium">
                          {conversationDetails?.duration || 'Calculando...'}
                        </div>
                      </div>
                      <div className="bg-muted/50 p-4 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-1">Avaliação</div>
                        <div className="font-medium text-2xl">
                          {getCSATEmoji(conversationDetails?.csat_rating) || '-'}
                        </div>
                      </div>
                    </div>

                    {/* Informações da Conversa */}
                    <div className="bg-muted/50 p-4 rounded-lg">
                      <div className="flex items-center gap-2 mb-3">
                        {getChannelIcon(conversationDetails?.inbox?.channel_type)}
                        <span className="font-medium">
                          {conversationDetails?.inbox?.channel_type === 'whatsapp' ? 'WhatsApp' :
                           conversationDetails?.inbox?.channel_type === 'telegram' ? 'Telegram' :
                           conversationDetails?.inbox?.channel_type === 'email' ? 'Email' :
                           conversationDetails?.inbox?.channel_type || 'WhatsApp'}
                        </span>
                        <span className="text-sm text-muted-foreground ml-auto">
                          Início: {conversationDetails?.created_at ? 
                            new Date(conversationDetails.created_at).toLocaleString('pt-BR') : 
                            'Data não disponível'}
                        </span>
                      </div>
                    </div>

                    {/* Histórico da Conversa */}
                    <div className="bg-muted/50 p-4 rounded-lg">
                      <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="w-5 h-5" />
                        <h3 className="font-semibold">Histórico da Conversa</h3>
                        <span className="text-sm text-muted-foreground ml-auto">
                          {conversationMessages.length} mensagens
                        </span>
                      </div>
                      
                      {loadingMessages ? (
                        <div className="text-center py-8">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                          <p className="mt-2 text-sm text-muted-foreground">Carregando mensagens...</p>
                        </div>
                      ) : conversationMessages.length > 0 ? (
                        <div className="space-y-3 max-h-80 overflow-y-auto">
                          {conversationMessages.map((message, index) => (
                            <div key={index} className="flex gap-3 p-3 bg-background rounded-lg">
                              <div className="flex-shrink-0">
                                {message.message_type === 'outgoing' ? (
                                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-blue-600" />
                                  </div>
                                ) : (
                                  <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                                    <User className="w-4 h-4 text-gray-600" />
                                  </div>
                                )}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-sm font-medium">
                                    {message.message_type === 'outgoing' ? 'Sistema' : 
                                     (conversationDetails?.contact?.name || 'Cliente')}
                                  </span>
                                  <span className="text-xs text-muted-foreground">
                                    {message.created_at ? 
                                      new Date(message.created_at).toLocaleTimeString('pt-BR') : 
                                      'Horário não disponível'}
                                  </span>
                                </div>
                                <div className="text-sm text-foreground">
                                  {message.content || message.text || 'Mensagem sem conteúdo'}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-muted-foreground">
                          <MessageSquare className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                          <p>Nenhuma mensagem encontrada para esta conversa.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
