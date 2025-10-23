import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, Download, FastForward } from 'lucide-react';

export default function CustomAudioPlayer({ src, isCustomer }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [blobUrl, setBlobUrl] = useState(null);


  // Reset state when src changes
  useEffect(() => {
    setLoading(true);
    setIsLoaded(false);
    setError(null);
    setProgress(0);
    setDuration(0);
    setPlaying(false);
    
    // Limpar blob URL anterior
    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
      setBlobUrl(null);
    }

    // Se a URL é externa (não localhost) E não é uma URL relativa, tentar baixar via fetch
    if (src && 
        !src.startsWith('data:') && 
        !src.startsWith('/') && 
        !src.includes('localhost') && 
        !src.includes('192.168.') &&
        (src.startsWith('http://') || src.startsWith('https://'))) {
      // Verificar se a URL parece válida antes de tentar baixar
      if (src.includes('/api/media/') && !src.includes('audio_17')) {
        downloadExternalAudio(src);
      } else {
        // URL suspeita ou inválida, usar diretamente
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [src]);

  const downloadExternalAudio = async (url) => {
    try {
      // Verificar se a URL é válida antes de tentar baixar
      if (!url || url.includes('audio_17') || !url.includes('/api/media/')) {
        setError('URL de áudio inválida');
        setLoading(false);
        return;
      }

      const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'audio/*,video/*,*/*'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      const newBlobUrl = URL.createObjectURL(blob);
      
      setBlobUrl(newBlobUrl);
      setError(null);
    } catch (error) {
      setError(`Erro ao baixar áudio: ${error.message}`);
      setLoading(false);
    }
  };

  const togglePlay = async () => {
    // Tentando reproduzir áudio
    
    if (!audioRef.current) {
      setError('Elemento de áudio não encontrado');
      return;
    }

    if (loading) {
      setError('Aguarde o áudio carregar...');
      return;
    }

    if (!isLoaded) {
      // Tentar recarregar o áudio
      audioRef.current.load();
      setError('Tentando carregar áudio...');
      return;
    }
    
    try {
      if (playing) {
        audioRef.current.pause();
      } else {
        await audioRef.current.play();
      }
    } catch (e) {
      console.error(' Erro ao reproduzir áudio:', e);
      setError(`Erro ao reproduzir: ${e.message}`);
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !audioRef.current.muted;
    setMuted(audioRef.current.muted);
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    setProgress(audioRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    if (!audioRef.current) return;
    const duration = audioRef.current.duration;
    // Metadados carregados
    
    // Verificar se a duração é válida (não é Infinity, NaN ou negativa)
    if (isFinite(duration) && duration > 0 && duration !== Infinity) {
      setDuration(duration);
      setIsLoaded(true);
      setLoading(false);
      setError(null);
      // Áudio carregado com sucesso
    } else {
      // Duração inválida, aguardando metadados
      // Tentar aguardar um pouco mais para os metadados carregarem completamente
      setTimeout(() => {
        if (audioRef.current && isFinite(audioRef.current.duration) && audioRef.current.duration > 0) {
          setDuration(audioRef.current.duration);
          setIsLoaded(true);
          setLoading(false);
          setError(null);
          // Áudio carregado após timeout
        } else {
          // Se ainda não carregou, tentar reproduzir mesmo assim (para áudios ao vivo/streaming)
          // Tentando reproduzir áudio sem duração definida (streaming/ao vivo)
          setDuration(0); // Definir como 0 para áudios sem duração definida
          setIsLoaded(true);
          setLoading(false);
          setError(null);
        }
      }, 500);
    }
  };

  const handleProgressBarClick = (e) => {
    if (!audioRef.current) return;
    const rect = e.target.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const seekTime = percent * duration;
    audioRef.current.currentTime = seekTime;
    setProgress(seekTime);
  };

  const toggleSpeed = () => {
    let newSpeed = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    setSpeed(newSpeed);
    if (audioRef.current) {
      audioRef.current.playbackRate = newSpeed;
    }
  };

  // Format time in mm:ss
  const formatTime = (time) => {
    if (isNaN(time) || !isFinite(time) || time < 0) return '00:00';
    const min = Math.floor(time / 60);
    const sec = Math.floor(time % 60);
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  // Determinar qual URL usar
  const audioSrc = blobUrl || src;

  // Função para tentar recarregar o áudio
  const retryLoad = () => {
    if (audioRef.current) {
      // Tentando recarregar áudio
      setLoading(true);
      setError(null);
      audioRef.current.load();
    }
  };

  // Função para tentar diferentes formatos de áudio
  const tryDifferentFormats = async () => {
    if (!src) return;
    
    // Primeiro, verificar se o arquivo original existe
    try {
      const originalResponse = await fetch(src, { 
        method: 'HEAD',
        signal: AbortSignal.timeout(2000)
      });
      if (originalResponse.ok) {
        if (audioRef.current) {
          audioRef.current.src = src;
          audioRef.current.load();
          setError(null);
          return;
        }
      }
    } catch (error) {
      // Arquivo original não disponível, continuar com formatos alternativos
    }
    
    // Lista de formatos para tentar (apenas se o original não existir)
    const formats = [
      { ext: '.mp3', type: 'audio/mpeg' },
      { ext: '.ogg', type: 'audio/ogg' },
      { ext: '.wav', type: 'audio/wav' },
      { ext: '.m4a', type: 'audio/mp4' }
    ];
    
    for (const format of formats) {
      try {
        // Tentar com extensão diferente
        const testUrl = src.replace(/\.[^/.]+$/, format.ext);
        
        // Verificar se o arquivo existe antes de tentar carregar
        const response = await fetch(testUrl, { 
          method: 'HEAD',
          signal: AbortSignal.timeout(2000) // Timeout de 2 segundos
        });
        if (response.ok) {
          if (audioRef.current) {
            audioRef.current.src = testUrl;
            audioRef.current.load();
            setError(null);
            return;
          }
        }
      } catch (error) {
        // Silenciar todos os erros para evitar spam no console
      }
    }
    
    setError('Áudio não disponível - arquivo não encontrado');
  };

  // Função para normalizar URL
  const normalizeUrl = (url) => {
    if (!url) return null;
    
    // Se já é uma URL completa, retornar como está
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    
    // Se é uma URL relativa, adicionar o host atual
    if (url.startsWith('/')) {
      return `${window.location.origin}${url}`;
    }
    
    // Se não tem protocolo, assumir que é relativa
    return `${window.location.origin}/${url}`;
  };

  // Usar blobUrl apenas se existir, senão usar src normalizado
  const finalSrc = blobUrl || normalizeUrl(src);

  return (
    <div className={`flex flex-col gap-1 rounded-lg px-2 py-1 ${isCustomer ? 'bg-[#23272f]' : 'bg-[#009ca6]'} shadow`}>
      {error && (
        <div className="text-red-300 text-xs mb-1">
          {error}
          <button 
            onClick={retryLoad}
            className="ml-2 text-blue-300 underline hover:text-blue-200"
          >
            Tentar novamente
          </button>
          {error.includes('Formato não suportado') && (
            <button 
              onClick={tryDifferentFormats}
              className="ml-2 text-green-300 underline hover:text-green-200"
            >
              Tentar outros formatos
            </button>
          )}
        </div>
      )}
      {loading && !error && (
        <div className="text-blue-300 text-xs mb-1">
          Carregando áudio...
        </div>
      )}
      <div className="flex items-center gap-2">
        <button 
          onClick={togglePlay} 
          className="p-1 text-white"
          disabled={loading}
        >
          {playing ? <Pause size={20} /> : <Play size={20} />}
        </button>
        <span className="text-xs text-white min-w-[48px]">
          {formatTime(progress)} / {formatTime(duration)}
        </span>
        <button onClick={toggleSpeed} className="p-1 text-white flex items-center">
          <FastForward size={18} />
          <span className="ml-1 text-xs">{speed}x</span>
        </button>
        <a href={src} download target="_blank" rel="noopener noreferrer" className="p-1 text-white">
          <Download size={18} />
        </a>
        <button onClick={toggleMute} className="p-1 text-white">
          <Volume2 size={18} />
        </button>
      </div>
      <div className="w-full h-2 bg-gray-300 rounded cursor-pointer" onClick={handleProgressBarClick} style={{ position: 'relative' }}>
        <div
          className="h-2 bg-blue-500 rounded"
          style={{ width: duration > 0 ? `${(progress / duration) * 100}%` : '0%' }}
        ></div>
      </div>
      <audio
        ref={audioRef}
        src={finalSrc}
        preload="metadata"
        onLoadStart={() => {
          setLoading(true);
          setError(null);
        }}
        onCanPlay={() => {
          // Áudio pode ser reproduzido
        }}
        onCanPlayThrough={() => {
          // Áudio pode ser reproduzido completamente
        }}
        onLoadedMetadata={() => {
          handleLoadedMetadata();
        }}
        onDurationChange={() => {
          if (audioRef.current && isFinite(audioRef.current.duration) && audioRef.current.duration > 0) {
            setDuration(audioRef.current.duration);
            setIsLoaded(true);
            setLoading(false);
            setError(null);
          }
        }}
        onLoadedData={() => {
          // Dados do áudio carregados
        }}
        onPlay={() => {
          setPlaying(true);
          setError(null);
        }}
        onPause={() => {
          setPlaying(false);
        }}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => {
          setPlaying(false);
        }}
        onError={(e) => {
          // Erro de reprodução de áudio
          
          let errorMessage = 'Erro desconhecido';
          if (audioRef.current?.error) {
            switch (audioRef.current.error.code) {
              case 1:
                errorMessage = 'Operação abortada';
                break;
              case 2:
                errorMessage = 'Erro de rede - verifique a conexão';
                break;
              case 3:
                errorMessage = 'Erro de decodificação - formato não suportado';
                break;
              case 4:
                errorMessage = 'Formato não suportado pelo navegador';
                break;
              default:
                errorMessage = audioRef.current.error.message || 'Erro de reprodução';
            }
          } else {
            // Se não há erro específico, verificar network state
            if (audioRef.current?.networkState === 3) {
              errorMessage = 'Erro de rede - arquivo não encontrado';
            } else if (audioRef.current?.readyState === 0) {
              errorMessage = 'Arquivo não carregado - verifique a URL';
            }
          }
          
          // Se for erro de formato não suportado, tentar outros formatos
          if (audioRef.current?.error?.code === 4 || audioRef.current?.error?.code === 3) {
            // Formato não suportado, tentando outros formatos
            tryDifferentFormats();
            setError('Tentando formatos alternativos...');
            return;
          }
          
          setError(`Erro ao carregar áudio: ${errorMessage}`);
          setLoading(false);
          setIsLoaded(false);
        }}
        onAbort={() => {
          // Carregamento do áudio abortado
          setLoading(false);
        }}
        onSuspend={() => {
          // Carregamento do áudio suspenso
        }}
        style={{ display: 'none' }}
        crossOrigin="anonymous"
      />
    </div>
  );
} 