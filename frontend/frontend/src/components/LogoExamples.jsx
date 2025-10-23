import React from 'react';
import NioChatLogo, { NioChatIcon } from './NioChatLogo';

const LogoExamples = () => {
  return (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Nova Logo Nio Chat</h2>
      
      {/* Logo Principal */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Logo Principal</h3>
        <div className="flex items-center gap-8">
          <NioChatLogo size={64} />
          <NioChatLogo size={48} />
          <NioChatLogo size={32} />
        </div>
      </div>

      {/* Logo sem texto */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Logo sem Texto</h3>
        <div className="flex items-center gap-8">
          <NioChatLogo size={64} showText={false} />
          <NioChatLogo size={48} showText={false} />
          <NioChatLogo size={32} showText={false} />
        </div>
      </div>

      {/* Ícones pequenos */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Ícones</h3>
        <div className="flex items-center gap-8">
          <NioChatIcon size={32} />
          <NioChatIcon size={24} />
          <NioChatIcon size={16} />
        </div>
      </div>

      {/* Modo escuro */}
      <div className="space-y-4 bg-gray-900 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white">Modo Escuro</h3>
        <div className="flex items-center gap-8">
          <NioChatLogo size={48} darkMode={true} />
          <NioChatLogo size={32} showText={false} darkMode={true} />
          <NioChatIcon size={24} />
        </div>
      </div>

      {/* Exemplos de uso */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Exemplos de Uso</h3>
        
        {/* Header */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <NioChatLogo size={40} />
            <div className="text-sm text-gray-600">
              Header da aplicação
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <NioChatIcon size={20} />
            <span className="text-sm font-medium">Menu lateral</span>
          </div>
        </div>

        {/* Loading */}
        <div className="border rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin">
              <NioChatIcon size={24} />
            </div>
            <span className="text-sm">Carregando...</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogoExamples;


