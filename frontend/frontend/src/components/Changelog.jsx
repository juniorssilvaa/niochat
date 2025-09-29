import React, { useState, useEffect } from 'react';
import { X, Calendar, Package, Sparkles, Shield, Zap, Database, Bug, Plus, Settings } from 'lucide-react';

const Changelog = ({ isOpen, onClose }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentVersion, setCurrentVersion] = useState('2.23.2');

  useEffect(() => {
    const loadChangelog = async () => {
      try {
        setLoading(true);
        // Carregar dados do backend
        const response = await fetch('/api/changelog/');
        if (response.ok) {
          const data = await response.json();
          setVersions(data.versions || []);
          setCurrentVersion(data.current_version || '2.23.2');
        } else {
          // Fallback para dados estáticos se a API falhar
          setVersions(fallbackVersions);
        }
      } catch (error) {
        console.error('Erro ao carregar changelog:', error);
        // Usar dados estáticos como fallback
        setVersions(fallbackVersions);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadChangelog();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Dados fallback caso o arquivo não carregue
  const fallbackVersions = [
    {
      version: "2.8.4",
      date: "2025-09-26",
      type: "patch",
      title: "Correções e Melhorias",
      changes: [
        {
          type: "fix",
          icon: <Bug className="w-4 h-4" />,
          title: "Separação de Sons por Categoria",
          description: "Corrigido sistema de sons na aba perfil - sons de mensagens e conversas agora são separados por categoria"
        },
        {
          type: "fix",
          icon: <Bug className="w-4 h-4" />,
          title: "Chat Interno",
          description: "Corrigido problema de envio de mensagens no chat interno"
        },
        {
          type: "fix",
          icon: <Bug className="w-4 h-4" />,
          title: "Interface do Chat",
          description: "Removidos ícones desnecessários (telefone, câmera, 3 pontos) do chat interno"
        }
      ]
    },
    {
      version: "2.8.3",
      date: "2025-09-26",
      type: "minor",
      title: "Sistema de Chat e Processamento de Mídia",
      changes: [
        {
          type: "feature",
          icon: <Sparkles className="w-4 h-4" />,
          title: "Processamento de PDFs",
          description: "Implementado sistema completo para análise de documentos PDF"
        },
        {
          type: "feature",
          icon: <Zap className="w-4 h-4" />,
          title: "Análise de Imagens com IA",
          description: "Detecção automática de problemas técnicos (LED vermelho em modems)"
        },
        {
          type: "fix",
          icon: <Bug className="w-4 h-4" />,
          title: "Integração WhatsApp",
          description: "Corrigido endpoint de envio de mensagens (Uazapi)"
        }
      ]
    },
    {
      version: "2.1.5",
      date: "2025-01-23",
      type: "major",
      title: "Sistema CSAT e Auditoria Avançada",
      changes: [
        {
          type: "feature",
          icon: <Sparkles className="w-4 h-4" />,
          title: "Sistema CSAT Completo",
          description: "Coleta automática de feedback com dashboard interativo e métricas em tempo real"
        },
        {
          type: "feature", 
          icon: <Zap className="w-4 h-4" />,
          title: "Análise de Sentimento IA",
          description: "Interpretação automática de feedback textual convertendo em avaliações CSAT"
        },
        {
          type: "feature",
          icon: <Shield className="w-4 h-4" />,
          title: "Auditoria Avançada",
          description: "Histórico completo de conversas com avaliações CSAT integradas"
        },
        {
          type: "improvement",
          icon: <Database className="w-4 h-4" />,
          title: "Isolamento de Dados",
          description: "Segurança total entre provedores com dados completamente isolados"
        },
        {
          type: "improvement",
          icon: <Settings className="w-4 h-4" />,
          title: "Interface Otimizada",
          description: "Componentes redesenhados sem emojis para aparência mais profissional"
        },
        {
          type: "fix",
          icon: <Bug className="w-4 h-4" />,
          title: "Limpeza de Dados",
          description: "Remoção completa de dados mockados e otimização do sistema"
        }
      ]
    },
    {
      version: "2.0.0",
      date: "2024-12-15",
      type: "major",
      title: "IA Inteligente + SGP",
      changes: [
        {
          type: "feature",
          icon: <Sparkles className="w-4 h-4" />,
          title: "Integração ChatGPT",
          description: "IA conversacional avançada com personalidade customizável"
        },
        {
          type: "feature",
          icon: <Database className="w-4 h-4" />,
          title: "SGP Automático",
          description: "Consulta dados reais do cliente via Function Calls"
        },
        {
          type: "feature",
          icon: <Zap className="w-4 h-4" />,
          title: "Fluxo Inteligente",
          description: "Detecção automática de demandas sem perguntas desnecessárias"
        },
        {
          type: "feature",
          icon: <Package className="w-4 h-4" />,
          title: "Geração Automática",
          description: "Faturas com PIX e QR Code automático"
        }
      ]
    },
    {
      version: "1.0.0",
      date: "2024-08-15",
      type: "major",
      title: "Lançamento Inicial",
      changes: [
        {
          type: "feature",
          icon: <Plus className="w-4 h-4" />,
          title: "Sistema Base Completo",
          description: "Integração com Uazapi/Evolution, interface React moderna"
        },
        {
          type: "feature",
          icon: <Zap className="w-4 h-4" />,
          title: "WebSocket em Tempo Real",
          description: "Sistema de reações e exclusão de mensagens"
        },
        {
          type: "feature",
          icon: <Settings className="w-4 h-4" />,
          title: "Sistema Multi-tenant",
          description: "Gestão de equipes e permissões granulares"
        },
        {
          type: "feature",
          icon: <Package className="w-4 h-4" />,
          title: "Integrações Múltiplas",
          description: "WhatsApp, Telegram, Email, Webchat"
        }
      ]
    }
  ];

  const getTypeColor = (type) => {
    switch (type) {
      case 'feature':
        return 'text-green-400 bg-green-400/10';
      case 'improvement':
        return 'text-blue-400 bg-blue-400/10';
      case 'fix':
        return 'text-yellow-400 bg-yellow-400/10';
      default:
        return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getVersionTypeColor = (type) => {
    switch (type) {
      case 'major':
        return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
      case 'minor':
        return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case 'patch':
        return 'text-green-400 bg-green-400/10 border-green-400/20';
      default:
        return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getChangeIcon = (type) => {
    switch (type) {
      case 'feature':
        return <Sparkles className="w-4 h-4" />;
      case 'improvement':
        return <Zap className="w-4 h-4" />;
      case 'fix':
        return <Bug className="w-4 h-4" />;
      case 'security':
        return <Shield className="w-4 h-4" />;
      default:
        return <Plus className="w-4 h-4" />;
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'feature':
        return 'Novo';
      case 'improvement':
        return 'Melhoria';
      case 'fix':
        return 'Correção';
      case 'security':
        return 'Segurança';
      default:
        return '';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-sidebar border border-border rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6 text-primary" />
            <div>
              <h2 className="text-xl font-semibold text-sidebar-foreground">Changelog</h2>
              <p className="text-sm text-muted-foreground">Atualizações e melhorias do sistema</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-100px)]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Carregando changelog...</span>
            </div>
          ) : (
            <div className="space-y-8">
              {versions.map((version, index) => (
              <div key={version.version} className="relative">
                {/* Version Header */}
                <div className="flex items-center gap-4 mb-4">
                  <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getVersionTypeColor(version.type)}`}>
                    v{version.version}
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Calendar className="w-4 h-4" />
                    {new Date(version.date).toLocaleDateString('pt-BR')}
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-sidebar-foreground mb-4">
                  {version.title}
                </h3>

                {/* Changes */}
                <div className="space-y-3 mb-6">
                  {version.changes.map((change, changeIndex) => (
                    <div
                      key={changeIndex}
                      className="flex items-start gap-3 p-3 rounded-lg bg-sidebar-accent/50"
                    >
                      <div className={`p-1.5 rounded-lg ${getTypeColor(change.type)}`}>
                        {getChangeIcon(change.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(change.type)}`}>
                            {getTypeLabel(change.type)}
                          </span>
                          <h4 className="font-medium text-sidebar-foreground">
                            {change.title}
                          </h4>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {change.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Divider */}
                {index < versions.length - 1 && (
                  <div className="border-b border-border"></div>
                )}
              </div>
            ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border bg-sidebar-accent/20">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div>
              Sistema Nio Chat - Versão atual: <span className="text-primary font-medium">{currentVersion}</span>
            </div>
            <div>
              Sistema Nio Chat
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Changelog;
