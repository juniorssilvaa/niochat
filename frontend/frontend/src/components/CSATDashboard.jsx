import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement, BarElement } from 'chart.js';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { MessageCircle, TrendingUp, Users, Clock } from 'lucide-react';
import axios from 'axios';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
);

export default function CSATDashboard({ provedorId }) {
  // Estado para dados CSAT (sem mock data)
  const [csatData, setCsatData] = useState({
    total_feedbacks: 0,
    average_rating: 0,
    satisfaction_rate: 0,
    rating_distribution: [],
    channel_distribution: [],
    daily_stats: [],
    recent_feedbacks: []
  });
  
  const [loading, setLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState(30);

  // Carregar dados do CSAT
  useEffect(() => {
    fetchCSATData();
  }, [timeFilter, provedorId]);

  const fetchCSATData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/csat/feedbacks/stats/?days=${timeFilter}`, {
        headers: { Authorization: `Token ${token}` }
      });
      setCsatData(response.data);
    } catch (error) {
      console.error('Erro ao carregar dados CSAT:', error);
      // Manter dados vazios em caso de erro
      setCsatData({
        total_feedbacks: 0,
        average_rating: 0,
        satisfaction_rate: 0,
        rating_distribution: [],
        channel_distribution: [],
        daily_stats: [],
        recent_feedbacks: []
      });
    } finally {
      setLoading(false);
    }
  };

  // Configuração do gráfico de rosca (Distribuição das Avaliações)
  const doughnutData = {
    labels: ['😡 Muito insatisfeito', '😕 Insatisfeito', '😐 Neutro', '🙂 Satisfeito', '🤩 Muito satisfeito'],
    datasets: [
      {
        data: csatData.rating_distribution.map(item => item.count),
        backgroundColor: [
          '#ef4444', // Vermelho para 😡
          '#f97316', // Laranja para 😕
          '#eab308', // Amarelo para 😐
          '#22c55e', // Verde para 🙂
          '#3b82f6', // Azul para 🤩
        ],
        borderWidth: 0,
      },
    ],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
        },
      },
    },
  };

  // Configuração do gráfico de linha (Evolução Temporal)
  const lineData = {
    labels: csatData.daily_stats.map(item => {
      const date = new Date(item.day);
      return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}`;
    }),
    datasets: [
      {
        label: 'Satisfação Média',
        data: csatData.daily_stats.map(item => item.avg_rating || 0),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#10b981',
        pointBorderWidth: 0,
      },
    ],
  };

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#ffffff',
        borderColor: '#10b981',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          label: function(context) {
            return `Satisfação: ${context.parsed.y.toFixed(1)}/5.0`;
          }
        }
      },
    },
    scales: {
      y: {
        display: false,
        beginAtZero: true,
        max: 5,
      },
      x: {
        display: false,
      }
    },
    interaction: {
      mode: 'index',
      intersect: false,
    },
    elements: {
      line: {
        tension: 0.4
      }
    }
  };

  // Configuração do gráfico de barras (Canais)
  const barData = {
    labels: csatData.channel_distribution.map(item => {
      const channelNames = {
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram',
        'web': 'Web Chat',
        'email': 'Email'
      };
      return channelNames[item.channel_type] || item.channel_type;
    }),
    datasets: [
      {
        label: 'Feedbacks por canal',
        data: csatData.channel_distribution.map(item => item.count),
        backgroundColor: [
          '#22c55e', // Verde para WhatsApp
          '#3b82f6', // Azul para Telegram
          '#8b5cf6', // Roxo para Web
          '#f59e0b', // Laranja para Email
        ],
        borderRadius: 4,
      },
    ],
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        },
      },
    },
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
          <h1 className="text-3xl font-bold text-foreground mb-2">CSAT - Satisfação do Cliente</h1>
          <p className="text-muted-foreground">
            Acompanhe a satisfação dos seus clientes através das avaliações coletadas automaticamente.
          </p>
        </div>

        {/* Filtro de Período */}
        <div className="mb-6">
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(parseInt(e.target.value))}
            className="px-4 py-2 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Últimos 7 dias</option>
            <option value={30}>Últimos 30 dias</option>
            <option value={90}>Últimos 90 dias</option>
          </select>
        </div>

        {/* Cards de Métricas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
          {/* Satisfação Média */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-lg">😊</span>
              <span className="text-sm font-medium text-muted-foreground">Satisfação Média</span>
            </div>
            <div className="text-3xl font-bold text-foreground">
              {csatData.average_rating}
            </div>
            <div className="text-sm text-muted-foreground">
              de 5.0 pontos
            </div>
          </div>

          {/* Total Avaliações */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <div className="flex items-center gap-3 mb-2">
              <MessageCircle className="w-5 h-5 text-blue-500" />
              <span className="text-sm font-medium text-muted-foreground">Total de Avaliações</span>
            </div>
            <div className="text-3xl font-bold text-foreground">
              {csatData.total_feedbacks}
            </div>
            <div className="text-sm text-muted-foreground">
              nos últimos {timeFilter} dias
            </div>
          </div>

          {/* Taxa de Satisfação */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-muted-foreground">Taxa de Satisfação</span>
            </div>
            <div className="text-3xl font-bold text-foreground">
              {csatData.satisfaction_rate}%
            </div>
            <div className="text-sm text-muted-foreground">
              clientes satisfeitos
            </div>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Distribuição das Avaliações */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <h3 className="text-lg font-semibold mb-4 text-foreground">Distribuição das Avaliações</h3>
            <div className="h-80">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : csatData.rating_distribution.length > 0 ? (
                <Doughnut data={doughnutData} options={doughnutOptions} />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <MessageCircle className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p>Nenhuma avaliação encontrada</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Evolução Temporal */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <h3 className="text-lg font-semibold mb-4 text-foreground">Evolução Temporal</h3>
            <div className="h-80">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : csatData.daily_stats.length > 0 ? (
                <Line data={lineData} options={lineOptions} />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <TrendingUp className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p>Nenhum dado temporal encontrado</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Feedbacks por Canal */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-card p-6 rounded-lg border border-border">
            <h3 className="text-lg font-semibold mb-4 text-foreground">Feedbacks por Canal</h3>
            <div className="h-80">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : csatData.channel_distribution.length > 0 ? (
                <Bar data={barData} options={barOptions} />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <Users className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p>Nenhum dado de canal encontrado</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Últimos Feedbacks */}
          <div className="bg-card p-6 rounded-lg border border-border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">Últimos Feedbacks</h3>
              {csatData.recent_feedbacks && csatData.recent_feedbacks.length > 3 && (
                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  {csatData.recent_feedbacks.length} feedbacks • Role para ver mais
                </span>
              )}
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto pr-2" style={{
              scrollbarWidth: 'thin',
              scrollbarColor: '#9CA3AF #E5E7EB'
            }}>
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : csatData.recent_feedbacks && csatData.recent_feedbacks.length > 0 ? (
                csatData.recent_feedbacks.map((feedback, index) => (
                  <div key={index} className="flex items-start gap-4 p-4 bg-background rounded border border-border">
                    {/* Foto do cliente */}
                    <div className="flex-shrink-0">
                      {feedback.contact_photo ? (
                        <img 
                          src={feedback.contact_photo} 
                          alt={feedback.contact_name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center">
                          <span className="text-white text-sm font-medium">
                            {feedback.contact_name?.charAt(0) || '?'}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    {/* Conteúdo do feedback */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="font-medium text-foreground">
                            {feedback.contact_name || 'Cliente'}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Conversa #{feedback.conversation} • {feedback.channel_type}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(feedback.feedback_sent_at).toLocaleString('pt-BR')}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{feedback.emoji_rating}</span>
                          <span className={`px-2 py-1 text-xs font-medium text-white rounded-full ${
                            feedback.rating_value <= 2 ? 'bg-red-500' : 
                            feedback.rating_value === 3 ? 'bg-yellow-500' : 
                            'bg-green-500'
                          }`}>
                            {feedback.rating_value}
                          </span>
                        </div>
                      </div>
                      <div className="text-sm text-muted-foreground bg-muted/50 p-2 rounded">
                        "{feedback.original_message}"
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground">
                  <div className="text-center">
                    <MessageCircle className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
                    <p>Nenhum feedback recente encontrado</p>
                    <p className="text-sm">Os feedbacks dos clientes aparecerão aqui quando coletados.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}