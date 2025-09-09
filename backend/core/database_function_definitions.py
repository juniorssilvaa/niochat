# Ferramentas de banco de dados para OpenAI Function Calling
DATABASE_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_equipes_disponiveis",
            "description": "Busca todas as equipes disponíveis no sistema. Use quando precisar listar equipes para transferência de conversas.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_membro_disponivel_equipe",
            "description": "Busca membros disponíveis de uma equipe específica. Use quando precisar transferir conversa para um membro específico da equipe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_equipe": {
                        "type": "string",
                        "description": "Nome da equipe para buscar membros disponíveis"
                    }
                },
                "required": ["nome_equipe"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "executar_transferencia_conversa",
            "description": "Executa transferência de conversa para uma equipe específica. Use quando cliente solicitar atendimento de equipe específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "integer",
                        "description": "ID da conversa a ser transferida"
                    },
                    "equipe_nome": {
                        "type": "string",
                        "description": "Nome da equipe de destino"
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Motivo da transferência explicado em português"
                    }
                },
                "required": ["conversation_id", "equipe_nome", "motivo"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_conversas_ativas",
            "description": "Busca conversas ativas do provedor. Use para verificar status das conversas, relatórios ou quando precisar de informações sobre atendimentos em andamento.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transferir_conversa_inteligente",
            "description": "TRANSFERENCIA INTELIGENTE! Analisa automaticamente a conversa e transfere para a equipe mais adequada baseada no conteudo das mensagens. Use quando a IA nao conseguir resolver o problema do cliente e precisar transferir para equipe humana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "integer",
                        "description": "ID da conversa a ser transferida"
                    }
                },
                "required": ["conversation_id"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Mapeamento de nomes de função para implementação
DATABASE_FUNCTION_MAPPING = {
    "buscar_equipes_disponiveis": "buscar_equipes_disponíveis",
    "buscar_membro_disponivel_equipe": "buscar_membro_disponível_equipe",
    "executar_transferencia_conversa": "executar_transferencia_conversa",
    "transferir_conversa_inteligente": "transferir_conversa_inteligente",
    "buscar_conversas_ativas": "buscar_conversas_ativas"
}

# Instruções específicas para o sistema prompt
DATABASE_SYSTEM_INSTRUCTIONS = """
FERRAMENTAS DE BANCO DE DADOS DISPONÍVEIS:

**Para Transferências (PRIORITÁRIO):**
1. buscar_equipes_disponiveis() - Verificar equipes existentes
2. buscar_membro_disponivel_equipe(nome_equipe) - Verificar disponibilidade  
3. executar_transferencia_conversa(conversation_id, equipe_nome, motivo) - Transferir conversa
4. transferir_conversa_inteligente(conversation_id) - Transferência automática baseada no conteúdo

**Para Consultas:**
5. buscar_conversas_ativas() - Ver conversas em andamento

**REGRAS IMPORTANTES:**
- SEMPRE use buscar_equipes_disponiveis() ANTES de tentar transferir
- Use executar_transferencia_conversa() quando cliente solicitar equipe específica
- Use transferir_conversa_inteligente() quando IA não conseguir resolver e precisar transferir
- Motivo deve ser em português e explicar por que está transferindo

**EXEMPLOS CORRETOS:**
Cliente: "Preciso falar com o financeiro"
IA: executa executar_transferencia_conversa("FINANCEIRO", "Cliente solicitou atendimento financeiro")

Cliente: "Alguém para me ajudar aí?"
IA: executa executar_transferencia_conversa("ATENDIMENTO", "Cliente pediu ajuda de atendente")

Cliente: "Quero ajuda"
IA: executa executar_transferencia_conversa("ATENDIMENTO", "Cliente solicitou atendimento humano")

Resultado: Conversa move de "Com IA" para "Em Espera" + Notificação WebSocket

**EXEMPLO INCORRETO:**
Cliente: "Preciso do financeiro" 
IA: "Vou buscar suas faturas..." + executa buscar_faturas_vencidas
ERRADO! Cliente quer transferência, não fatura!
"""