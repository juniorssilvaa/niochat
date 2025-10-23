import React from 'react';

const NioChatLogo = ({ 
  size = 48, 
  className = "", 
  showText = true,
  textColor = "text-gray-800",
  darkMode = false 
}) => {
  const baseColor = darkMode ? "#FF6B35" : "#FF8C42"; // Laranja vibrante
  const eyeColor = "#4FC3F7"; // Azul claro
  const textColorClass = darkMode ? "text-white" : textColor;

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo SVG */}
      <svg 
        width={size} 
        height={size} 
        viewBox="0 0 48 48" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        {/* Cabeça do robô */}
        <rect 
          x="8" 
          y="12" 
          width="32" 
          height="24" 
          rx="6" 
          fill={baseColor}
          stroke={baseColor}
          strokeWidth="2"
        />
        
        {/* Olhos azuis */}
        <circle cx="18" cy="22" r="3" fill={eyeColor} />
        <circle cx="30" cy="22" r="3" fill={eyeColor} />
        
        {/* Antena/Sensor no topo */}
        <circle cx="24" cy="10" r="2" fill={baseColor} />
        
        {/* Ondas de sinal */}
        <path 
          d="M 24 8 Q 20 6 16 8 Q 12 10 8 12" 
          stroke={baseColor} 
          strokeWidth="2" 
          fill="none" 
          strokeLinecap="round"
        />
        <path 
          d="M 24 8 Q 28 6 32 8 Q 36 10 40 12" 
          stroke={baseColor} 
          strokeWidth="2" 
          fill="none" 
          strokeLinecap="round"
        />
        
        {/* Base/Neck */}
        <path 
          d="M 12 36 Q 24 42 36 36" 
          stroke={baseColor} 
          strokeWidth="3" 
          fill="none" 
          strokeLinecap="round"
        />
        
        {/* Detalhes adicionais - pequenos pontos de "processamento" */}
        <circle cx="16" cy="28" r="1" fill="rgba(255,255,255,0.3)" />
        <circle cx="24" cy="28" r="1" fill="rgba(255,255,255,0.3)" />
        <circle cx="32" cy="28" r="1" fill="rgba(255,255,255,0.3)" />
      </svg>
      
      {/* Texto do logo */}
      {showText && (
        <div className={`font-bold text-xl ${textColorClass}`}>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-yellow-500">
            Nio
          </span>
          <span className="text-gray-600 dark:text-gray-300">
            Chat
          </span>
        </div>
      )}
    </div>
  );
};

// Versão compacta para ícones pequenos
export const NioChatIcon = ({ size = 24, className = "" }) => {
  const baseColor = "#FF8C42";
  const eyeColor = "#4FC3F7";

  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Cabeça do robô */}
      <rect 
        x="4" 
        y="6" 
        width="16" 
        height="12" 
        rx="3" 
        fill={baseColor}
      />
      
      {/* Olhos azuis */}
      <circle cx="9" cy="11" r="1.5" fill={eyeColor} />
      <circle cx="15" cy="11" r="1.5" fill={eyeColor} />
      
      {/* Antena */}
      <circle cx="12" cy="5" r="1" fill={baseColor} />
      
      {/* Ondas de sinal */}
      <path 
        d="M 12 4 Q 10 3 8 4" 
        stroke={baseColor} 
        strokeWidth="1" 
        fill="none" 
        strokeLinecap="round"
      />
      <path 
        d="M 12 4 Q 14 3 16 4" 
        stroke={baseColor} 
        strokeWidth="1" 
        fill="none" 
        strokeLinecap="round"
      />
      
      {/* Base */}
      <path 
        d="M 6 18 Q 12 21 18 18" 
        stroke={baseColor} 
        strokeWidth="1.5" 
        fill="none" 
        strokeLinecap="round"
      />
    </svg>
  );
};

export default NioChatLogo;


