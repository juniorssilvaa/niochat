import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Clock, MessageSquare } from "lucide-react";

export default function AgentPerformanceTable() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem('token');
        
        // Buscar dados de performance dos agentes da API do dashboard
        const dashboardResponse = await fetch('/api/dashboard/stats/', {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (dashboardResponse.ok) {
          const dashboardData = await dashboardResponse.json();
          setAgents(dashboardData.atendentes || []);
        }

        setLoading(false);
      } catch (error) {
        console.error('Erro ao buscar dados:', error);
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const performanceData = useMemo(() => {
    // Usar dados reais da API do dashboard
    return agents.map((agent, index) => {
      return {
        id: agent.id || `agent-${index}`, // Garantir ID único
        name: agent.name || 'Agente',
        email: agent.email || '',
        conversations: agent.conversations || 0,
        csat: agent.csat > 0 ? agent.csat.toFixed(1) : "-",
        responseTime: agent.responseTime > 0 ? agent.responseTime.toFixed(1) : "-",
        recent_emojis: agent.recent_emojis || []
      };
    });
  }, [agents]);

  if (loading) {
    return (
      <Card className="nc-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-foreground flex items-center gap-2">
          <Clock className="w-4 h-4 text-primary" />
          Performance por Atendente (Tempo de Resposta)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border border-border overflow-hidden">
          <Table>
            <TableHeader className="bg-muted">
              <TableRow>
                <TableHead className="text-foreground">Atendente</TableHead>
                <TableHead className="text-foreground">Conversas</TableHead>
                <TableHead className="text-foreground">CSAT</TableHead>
                <TableHead className="text-foreground">Resp. Média (min)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {performanceData.map(row => (
                <TableRow key={row.id} className="hover:bg-muted/50">
                  <TableCell className="font-medium text-foreground">{row.name}</TableCell>
                  <TableCell className="text-foreground">
                    <div className="flex items-center gap-1">
                      <MessageSquare className="w-3.5 h-3.5 text-primary" /> 
                      {row.conversations}
                    </div>
                  </TableCell>
                  <TableCell className="text-foreground">
                    <div className="flex items-center gap-2">
                      {/* Mostrar emojis reais recebidos */}
                      {row.recent_emojis && row.recent_emojis.length > 0 && (
                        <div className="flex gap-1">
                          {row.recent_emojis.slice(0, 3).map((emoji, index) => (
                            <span key={index} className="text-lg">
                              {emoji}
                            </span>
                          ))}
                        </div>
                      )}
                      <span className="text-sm text-muted-foreground">
                        {row.csat !== "-" ? `${row.csat}` : "-"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-foreground">{row.responseTime}</TableCell>
                </TableRow>
              ))}
              {performanceData.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground text-sm py-6">
                    Nenhum atendente encontrado.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}