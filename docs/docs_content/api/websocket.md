# WebSocket

O NioChat utiliza WebSocket para comunicação em tempo real entre o frontend e backend. Este documento explica como implementar e usar WebSocket.

## Conexão

### URL de Conexão
```javascript
const ws = new WebSocket('ws://localhost:8010/ws/dashboard/');
```

### Com Autenticação
```javascript
const token = 'seu_token_aqui';
const ws = new WebSocket(`ws://localhost:8010/ws/dashboard/?token=${token}`);
```

## Implementação JavaScript

### Classe WebSocket
```javascript
class NioChatWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 5000;
    this.listeners = {};
  }

  connect() {
    const url = `ws://localhost:8010/ws/dashboard/?token=${this.token}`;
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = (event) => {
      console.log('WebSocket conectado');
      this.reconnectAttempts = 0;
      this.emit('connected', event);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Erro ao processar mensagem:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket desconectado:', event.code, event.reason);
      this.emit('disconnected', event);
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      this.emit('error', error);
    };
  }

  handleMessage(data) {
    const { type, data: messageData } = data;
    
    switch (type) {
      case 'chat_message':
        this.emit('chat_message', messageData);
        break;
      case 'message_reaction':
        this.emit('message_reaction', messageData);
        break;
      case 'message_deleted':
        this.emit('message_deleted', messageData);
        break;
      case 'dashboard_metrics':
        this.emit('dashboard_metrics', messageData);
        break;
      case 'csat_update':
        this.emit('csat_update', messageData);
        break;
      case 'audit_log':
        this.emit('audit_log', messageData);
        break;
      case 'user_status':
        this.emit('user_status', messageData);
        break;
      default:
        console.log('Tipo de mensagem desconhecido:', type);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Tentativa de reconexão ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Máximo de tentativas de reconexão atingido');
      this.emit('reconnect_failed');
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket não está conectado');
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Uso
const ws = new NioChatWebSocket('seu_token_aqui');

// Conectar
ws.connect();

// Escutar eventos
ws.on('chat_message', (data) => {
  console.log('Nova mensagem:', data);
});

ws.on('dashboard_metrics', (data) => {
  console.log('Métricas atualizadas:', data);
});

ws.on('csat_update', (data) => {
  console.log('CSAT atualizado:', data);
});

ws.on('connected', () => {
  console.log('Conectado ao WebSocket');
});

ws.on('disconnected', () => {
  console.log('Desconectado do WebSocket');
});

ws.on('error', (error) => {
  console.error('Erro no WebSocket:', error);
});
```

## Eventos Disponíveis

### Chat

#### Nova Mensagem
```javascript
{
  "type": "chat_message",
  "data": {
    "conversation_id": 1,
    "message": {
      "id": 1,
      "content": "Nova mensagem",
      "sender": "customer",
      "timestamp": "2024-01-01T10:00:00Z",
      "message_type": "text"
    }
  }
}
```

#### Reação a Mensagem
```javascript
{
  "type": "message_reaction",
  "data": {
    "message_id": 1,
    "reaction": "👍",
    "user_id": 1
  }
}
```

#### Mensagem Deletada
```javascript
{
  "type": "message_deleted",
  "data": {
    "message_id": 1,
    "deleted_by": 1
  }
}
```

### Dashboard

#### Métricas Atualizadas
```javascript
{
  "type": "dashboard_metrics",
  "data": {
    "total_conversations": 100,
    "open_conversations": 25,
    "closed_conversations": 75,
    "average_satisfaction": 4.2,
    "resolution_rate": 0.85,
    "response_time": 120
  }
}
```

#### CSAT Atualizado
```javascript
{
  "type": "csat_update",
  "data": {
    "conversation_id": 1,
    "rating": 5,
    "feedback": "Excelente atendimento!",
    "contact_name": "João Silva",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

#### Log de Auditoria
```javascript
{
  "type": "audit_log",
  "data": {
    "id": 1,
    "action": "conversation_created",
    "details": {
      "conversation_id": 1,
      "contact_name": "João Silva"
    },
    "user": {
      "id": 1,
      "username": "agente1"
    },
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Status do Usuário

#### Usuário Online/Offline
```javascript
{
  "type": "user_status",
  "data": {
    "user_id": 1,
    "status": "online",
    "last_seen": "2024-01-01T10:00:00Z"
  }
}
```

## Implementação React

### Hook useWebSocket
```javascript
import { useState, useEffect, useCallback } from 'react';

export const useWebSocket = (token) => {
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [csatUpdates, setCsatUpdates] = useState([]);

  const connect = useCallback(() => {
    if (!token) return;

    const websocket = new WebSocket(`ws://localhost:8010/ws/dashboard/?token=${token}`);
    
    websocket.onopen = () => {
      setConnected(true);
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'chat_message':
          setMessages(prev => [...prev, data.data]);
          break;
        case 'dashboard_metrics':
          setMetrics(data.data);
          break;
        case 'csat_update':
          setCsatUpdates(prev => [...prev, data.data]);
          break;
        default:
          console.log('Evento desconhecido:', data.type);
      }
    };

    websocket.onclose = () => {
      setConnected(false);
      setWs(null);
    };

    websocket.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
    };

    return websocket;
  }, [token]);

  useEffect(() => {
    const websocket = connect();
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }, [ws]);

  return {
    connected,
    messages,
    metrics,
    csatUpdates,
    sendMessage
  };
};
```

### Componente Dashboard
```javascript
import React from 'react';
import { useWebSocket } from './hooks/useWebSocket';

const Dashboard = ({ token }) => {
  const { connected, metrics, csatUpdates } = useWebSocket(token);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Status: {connected ? 'Conectado' : 'Desconectado'}</p>
      
      {metrics && (
        <div>
          <h2>Métricas</h2>
          <p>Total de Conversas: {metrics.total_conversations}</p>
          <p>Conversas Abertas: {metrics.open_conversations}</p>
          <p>Satisfação Média: {metrics.average_satisfaction}</p>
        </div>
      )}
      
      {csatUpdates.length > 0 && (
        <div>
          <h2>Últimos CSATs</h2>
          {csatUpdates.map((csat, index) => (
            <div key={index}>
              <p>{csat.contact_name}: {csat.rating} - {csat.feedback}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
```

## Implementação Vue.js

### Plugin WebSocket
```javascript
// websocket.js
export default {
  install(Vue) {
    Vue.prototype.$websocket = {
      ws: null,
      connected: false,
      listeners: {},

      connect(token) {
        this.ws = new WebSocket(`ws://localhost:8010/ws/dashboard/?token=${token}`);
        
        this.ws.onopen = () => {
          this.connected = true;
          this.emit('connected');
        };

        this.ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.data);
        };

        this.ws.onclose = () => {
          this.connected = false;
          this.emit('disconnected');
        };

        this.ws.onerror = (error) => {
          this.emit('error', error);
        };
      },

      send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify(data));
        }
      },

      on(event, callback) {
        if (!this.listeners[event]) {
          this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
      },

      off(event, callback) {
        if (this.listeners[event]) {
          this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
      },

      emit(event, data) {
        if (this.listeners[event]) {
          this.listeners[event].forEach(callback => callback(data));
        }
      },

      disconnect() {
        if (this.ws) {
          this.ws.close();
          this.ws = null;
        }
      }
    };
  }
};
```

### Componente Vue
```vue
<template>
  <div>
    <h1>Dashboard</h1>
    <p>Status: {{ connected ? 'Conectado' : 'Desconectado' }}</p>
    
    <div v-if="metrics">
      <h2>Métricas</h2>
      <p>Total de Conversas: {{ metrics.total_conversations }}</p>
      <p>Conversas Abertas: {{ metrics.open_conversations }}</p>
      <p>Satisfação Média: {{ metrics.average_satisfaction }}</p>
    </div>
    
    <div v-if="csatUpdates.length > 0">
      <h2>Últimos CSATs</h2>
      <div v-for="(csat, index) in csatUpdates" :key="index">
        <p>{{ csat.contact_name }}: {{ csat.rating }} - {{ csat.feedback }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      connected: false,
      metrics: null,
      csatUpdates: []
    };
  },

  mounted() {
    const token = localStorage.getItem('niochat_token');
    if (token) {
      this.$websocket.connect(token);
      
      this.$websocket.on('connected', () => {
        this.connected = true;
      });
      
      this.$websocket.on('disconnected', () => {
        this.connected = false;
      });
      
      this.$websocket.on('dashboard_metrics', (data) => {
        this.metrics = data;
      });
      
      this.$websocket.on('csat_update', (data) => {
        this.csatUpdates.push(data);
      });
    }
  },

  beforeDestroy() {
    this.$websocket.disconnect();
  }
};
</script>
```

## Implementação Angular

### Serviço WebSocket
```typescript
import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private ws: WebSocket;
  private connected = false;
  private messageSubject = new Subject<any>();

  connect(token: string): void {
    this.ws = new WebSocket(`ws://localhost:8010/ws/dashboard/?token=${token}`);
    
    this.ws.onopen = () => {
      this.connected = true;
      this.messageSubject.next({ type: 'connected' });
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
    };

    this.ws.onclose = () => {
      this.connected = false;
      this.messageSubject.next({ type: 'disconnected' });
    };

    this.ws.onerror = (error) => {
      this.messageSubject.next({ type: 'error', data: error });
    };
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  getMessages(): Observable<any> {
    return this.messageSubject.asObservable();
  }

  isConnected(): boolean {
    return this.connected;
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### Componente Angular
```typescript
import { Component, OnInit, OnDestroy } from '@angular/core';
import { WebSocketService } from './websocket.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-dashboard',
  template: `
    <div>
      <h1>Dashboard</h1>
      <p>Status: {{ connected ? 'Conectado' : 'Desconectado' }}</p>
      
      <div *ngIf="metrics">
        <h2>Métricas</h2>
        <p>Total de Conversas: {{ metrics.total_conversations }}</p>
        <p>Conversas Abertas: {{ metrics.open_conversations }}</p>
        <p>Satisfação Média: {{ metrics.average_satisfaction }}</p>
      </div>
      
      <div *ngIf="csatUpdates.length > 0">
        <h2>Últimos CSATs</h2>
        <div *ngFor="let csat of csatUpdates; let i = index">
          <p>{{ csat.contact_name }}: {{ csat.rating }} - {{ csat.feedback }}</p>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit, OnDestroy {
  connected = false;
  metrics: any = null;
  csatUpdates: any[] = [];
  private subscription: Subscription;

  constructor(private websocketService: WebSocketService) {}

  ngOnInit() {
    const token = localStorage.getItem('niochat_token');
    if (token) {
      this.websocketService.connect(token);
      
      this.subscription = this.websocketService.getMessages().subscribe(message => {
        switch (message.type) {
          case 'connected':
            this.connected = true;
            break;
          case 'disconnected':
            this.connected = false;
            break;
          case 'dashboard_metrics':
            this.metrics = message.data;
            break;
          case 'csat_update':
            this.csatUpdates.push(message.data);
            break;
        }
      });
    }
  }

  ngOnDestroy() {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
    this.websocketService.disconnect();
  }
}
```

## Tratamento de Erros

### Reconexão Automática
```javascript
class WebSocketWithReconnect {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      maxReconnectAttempts: 5,
      reconnectInterval: 5000,
      ...options
    };
    this.reconnectAttempts = 0;
    this.listeners = {};
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.ws.onclose = (event) => {
      this.emit('disconnected', event);
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      this.emit('error', error);
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data.data);
    };
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Tentativa de reconexão ${this.reconnectAttempts}/${this.options.maxReconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.options.reconnectInterval);
    } else {
      this.emit('reconnect_failed');
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket não está conectado');
    }
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

## Próximos Passos

1. [Endpoints](endpoints.md) - Explore todos os endpoints da API
2. [Autenticação](authentication.md) - Aprenda sobre autenticação
3. [Webhooks](webhooks.md) - Aprenda sobre webhooks
