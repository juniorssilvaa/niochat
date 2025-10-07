import React, { useState, useEffect } from 'react';
import { X, Calendar, Package, Sparkles, Shield, Zap, Database, Bug, Plus, Settings } from 'lucide-react';

const Changelog = ({ isOpen, onClose }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentVersion, setCurrentVersion] = useState('2.24.0');

  useEffect(() => {
    const loadChangelog = async () => {
      try {
        setLoading(true);
        // Carregar dados do backend
        const response = await fetch('/api/changelog/');
        if (response.ok) {
          let data = null;
          try {
            data = await response.json();
          } catch (e) {
            console.error('Erro ao interpretar JSON do changelog:', e);
          }
          // API pode retornar um array direto ou um objeto { versions: [...] }
          const versionsData = Array.isArray(data) ? data : (data?.versions || []);
          setVersions(Array.isArray(versionsData) ? versionsData : []);
          setCurrentVersion((data && (data.current_version || data.version)) || '2.24.0');
        } else {
          console.error('Erro ao carregar changelog do backend');
          setVersions([]);
        }
      } catch (error) {
        console.error('Erro ao carregar changelog:', error);
        setVersions([]);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen) {
      loadChangelog();
    }
  }, [isOpen]);

  if (!isOpen) return null;

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
        return 'Outro';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <Package className="w-6 h-6 text-blue-400" />
            <div>
              <h2 className="text-xl font-semibold text-white">Changelog</h2>
              <p className="text-sm text-gray-400">Histórico de atualizações do sistema</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
              <span className="ml-3 text-gray-400">Carregando changelog...</span>
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Nenhuma versão encontrada</p>
            </div>
          ) : (
            <div className="space-y-6">
              {versions.map((version, index) => (
                <div key={version.version} className="relative">
                  {/* Version Header */}
                  <div className="flex items-center gap-4 mb-4">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium border ${getVersionTypeColor(version?.type)}`}>
                      {(version?.type || 'patch').toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{version?.version || 'v0.0.0'}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Calendar className="w-4 h-4" />
                        <span>{version?.date ? formatDate(version.date) : 'Data não informada'}</span>
                      </div>
                    </div>
                    {index === 0 && (
                      <div className="ml-auto">
                        <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-blue-500/30">
                          Atual
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Version Title */}
                  <h4 className="text-base font-medium text-gray-200 mb-3">{version?.title || 'Atualizações'}</h4>

                  {/* Changes */}
                  <div className="space-y-3">
                    {(Array.isArray(version?.changes) ? version.changes : []).map((change, changeIndex) => (
                      <div key={changeIndex} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
                        <div className={`p-1.5 rounded-lg ${getTypeColor(change?.type)}`}>
                          {getChangeIcon(change?.type)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(change?.type)}`}>
                              {getTypeLabel(change?.type)}
                            </span>
                            {change?.title && (
                              <span className="text-sm font-medium text-gray-200">{change.title}</span>
                            )}
                          </div>
                          <p className="text-sm text-gray-300">
                            {typeof change === 'string' ? change : (change?.description || change?.text || 'Atualização')}
                          </p>
                        </div>
                      </div>
                    ))}
                    {(!Array.isArray(version?.changes) || version.changes.length === 0) && (
                      <div className="text-sm text-gray-400">Sem itens listados nesta versão.</div>
                    )}
                  </div>

                  {/* Separator */}
                  {index < versions.length - 1 && (
                    <div className="mt-6 mb-6 border-t border-gray-700"></div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-700 bg-gray-800/50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              Versão atual: <span className="text-blue-400 font-medium">{currentVersion}</span>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Changelog;