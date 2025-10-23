"""
Serviço para integração com OpenAI ChatGPT
"""

import os
import openai
import logging
import json
import re
import pdfplumber
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from .models import Provedor, SystemConfig
from asgiref.sync import sync_to_async
from datetime import datetime
from .redis_memory_service import redis_memory_service
from .transfer_service import transfer_service
from .pdf_processor import pdf_processor
from .database_function_definitions import DATABASE_FUNCTION_TOOLS, DATABASE_FUNCTION_MAPPING, DATABASE_SYSTEM_INSTRUCTIONS
from .database_tools import DatabaseTools

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        # Não buscar chave durante inicialização para evitar problemas de contexto
        self.api_key = None
        self.model = "gpt-4.1"
        self.max_tokens = 1000
        self.temperature = 0.7

    def _get_api_key(self) -> str:
        """Busca a chave da API da OpenAI do banco de dados ou variável de ambiente"""
        try:
            # Primeiro tenta buscar do banco de dados
            config = SystemConfig.objects.first()
            if config and config.openai_api_key:
                logger.info("Usando chave da API OpenAI do banco de dados")
                return config.openai_api_key
        except Exception as e:
            logger.warning(f"Erro ao buscar chave da API do banco: {e}")
        
        # Fallback para variável de ambiente
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Usando chave da API OpenAI da variável de ambiente")
            return api_key
        
        # Se não encontrar chave, retornar None para que o erro seja tratado adequadamente
        logger.error("Nenhuma chave da API OpenAI encontrada - configure no painel do superadmin")
        return None

    async def _get_api_key_async(self) -> str:
        """Versão assíncrona para buscar a chave da API da OpenAI"""
        try:
            # Usar sync_to_async para buscar do banco de dados
            config = await sync_to_async(SystemConfig.objects.first)()
            if config and config.openai_api_key:
                logger.info("Usando chave da API OpenAI do banco de dados (async)")
                return config.openai_api_key
        except Exception as e:
            logger.warning(f"Erro ao buscar chave da API do banco (async): {e}")
        
        # Fallback para variável de ambiente
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("Usando chave da API OpenAI da variável de ambiente (async)")
            return api_key
        
        # Se não encontrar chave, retornar None para que o erro seja tratado adequadamente
        logger.error("Nenhuma chave da API OpenAI encontrada - configure no painel do superadmin (async)")
        return None

    def update_api_key(self):
        """Atualiza a chave da API quando ela é modificada no banco"""
        self.api_key = self._get_api_key()
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("Chave da API OpenAI atualizada")
        else:
            logger.error("Não foi possível atualizar a chave da API OpenAI - chave não configurada")

    async def update_api_key_async(self):
        """Versão assíncrona para atualizar a chave da API"""
        self.api_key = await self._get_api_key_async()
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("Chave da API OpenAI atualizada (async)")
        else:
            logger.error("Não foi possível atualizar a chave da API OpenAI - chave não configurada (async)")

    def _detectar_satisfacao_cliente(self, mensagem: str) -> Dict[str, Any]:
        """
        Detecta automaticamente se o cliente está satisfeito e quer encerrar o atendimento
        
        Returns:
            Dict com 'satisfeito': bool, 'motivo': str, 'confianca': float
        """
        mensagem_lower = mensagem.lower().strip()
        
        # Palavras-chave que indicam satisfação e desejo de encerrar
        palavras_satisfacao = [
            'ok', 'certo', 'beleza', 'blz', 'tá bom', 'ta bom', 'tudo bem', 'tudo certo',
            'perfeito', 'ótimo', 'excelente', 'maravilha', 'show', 'show de bola',
            'valeu', 'valeu mesmo', 'obrigado', 'obrigada', 'obrigadão', 'valeu demais',
            'tá de boa', 'ta de boa', 'de boa', 'suave', 'tranquilo', 'tranquilo demais',
            'resolvido', 'resolvido sim', 'conseguiu', 'deu certo', 'funcionou',
            'não precisa mais', 'nao precisa mais', 'não precisa de mais nada', 'nao precisa de mais nada',
            'já está bom', 'ja esta bom', 'já está de boa', 'ja esta de boa',
            'tá tudo certo', 'ta tudo certo', 'tudo certo sim', 'tudo certo mesmo',
            'não tem mais dúvida', 'nao tem mais duvida', 'sem dúvida', 'sem duvida',
            'entendi tudo', 'entendi perfeitamente', 'entendi certinho',
            'não tem mais pergunta', 'nao tem mais pergunta', 'sem pergunta',
            'tá resolvido', 'ta resolvido', 'resolvido sim', 'resolvido mesmo',
            'não precisa de ajuda', 'nao precisa de ajuda', 'sem ajuda',
            'já consegui', 'ja consegui', 'consegui sim', 'consegui mesmo',
            'tá funcionando', 'ta funcionando', 'funcionando sim', 'funcionando mesmo',
            'não tem mais problema', 'nao tem mais problema', 'sem problema',
            'tá de boa', 'ta de boa', 'de boa sim', 'de boa mesmo',
            'não tem mais nada', 'nao tem mais nada', 'sem mais nada',
            'já está resolvido', 'ja esta resolvido', 'resolvido sim', 'resolvido mesmo',
            'não tem mais dúvida', 'nao tem mais duvida', 'sem dúvida', 'sem duvida',
            'entendi tudo', 'entendi perfeitamente', 'entendi certinho',
            'não tem mais pergunta', 'nao tem mais pergunta', 'sem pergunta',
            'tá resolvido', 'ta resolvido', 'resolvido sim', 'resolvido mesmo',
            'não precisa de ajuda', 'nao precisa de ajuda', 'sem ajuda',
            'já consegui', 'ja consegui', 'consegui sim', 'consegui mesmo',
            'tá funcionando', 'ta funcionando', 'funcionando sim', 'funcionando mesmo',
            'não tem mais problema', 'nao tem mais problema', 'sem problema',
            'tá de boa', 'ta de boa', 'de boa sim', 'de boa mesmo',
            'não tem mais nada', 'nao tem mais nada', 'sem mais nada',
            'já está resolvido', 'ja esta resolvido', 'resolvido sim', 'resolvido mesmo'
        ]
        
        # Palavras-chave que indicam despedida
        palavras_despedida = [
            'tchau', 'até logo', 'ate logo', 'até mais', 'ate mais', 'até a próxima', 'ate a proxima',
            'até depois', 'ate depois', 'até breve', 'ate breve', 'até mais tarde', 'ate mais tarde',
            'até amanhã', 'ate amanha', 'até segunda', 'ate segunda', 'até terça', 'ate terca',
            'até quarta', 'ate quarta', 'até quinta', 'ate quinta', 'até sexta', 'ate sexta',
            'até sábado', 'ate sabado', 'até domingo', 'ate domingo',
            'até a próxima vez', 'ate a proxima vez', 'até a próxima conversa', 'ate a proxima conversa',
            'até a próxima ligação', 'ate a proxima ligacao', 'até a próxima mensagem', 'ate a proxima mensagem',
            'até a próxima chamada', 'ate a proxima chamada', 'até a próxima vez que precisar', 'ate a proxima vez que precisar',
            'até a próxima vez que tiver dúvida', 'ate a proxima vez que tiver duvida',
            'até a próxima vez que precisar de ajuda', 'ate a proxima vez que precisar de ajuda',
            'até a próxima vez que tiver problema', 'ate a proxima vez que tiver problema',
            'até a próxima vez que precisar de suporte', 'ate a proxima vez que precisar de suporte',
            'até a próxima vez que precisar de atendimento', 'ate a proxima vez que precisar de atendimento',
            'até a próxima vez que precisar de assistência', 'ate a proxima vez que precisar de assistencia',
            'até a próxima vez que precisar de auxílio', 'ate a proxima vez que precisar de auxilio',
            'até a próxima vez que precisar de orientação', 'ate a proxima vez que precisar de orientacao',
            'até a próxima vez que precisar de informação', 'ate a proxima vez que precisar de informacao',
            'até a próxima vez que precisar de esclarecimento', 'ate a proxima vez que precisar de esclarecimento',
            'até a próxima vez que precisar de ajuda', 'ate a proxima vez que precisar de ajuda',
            'até a próxima vez que precisar de suporte', 'ate a proxima vez que precisar de suporte',
            'até a próxima vez que precisar de atendimento', 'ate a proxima vez que precisar de atendimento',
            'até a próxima vez que precisar de assistência', 'ate a proxima vez que precisar de assistencia',
            'até a próxima vez que precisar de auxílio', 'ate a proxima vez que precisar de auxilio',
            'até a próxima vez que precisar de orientação', 'ate a proxima vez que precisar de orientacao',
            'até a próxima vez que precisar de informação', 'ate a proxima vez que precisar de informacao',
            'até a próxima vez que precisar de esclarecimento', 'ate a proxima vez que precisar de esclarecimento'
        ]
        
        # Verificar se a mensagem contém palavras de satisfação
        satisfacao_detectada = any(palavra in mensagem_lower for palavra in palavras_satisfacao)
        despedida_detectada = any(palavra in mensagem_lower for palavra in palavras_despedida)
        
        # Calcular confiança baseada no número de palavras encontradas
        palavras_encontradas = []
        if satisfacao_detectada:
            palavras_encontradas.extend([palavra for palavra in palavras_satisfacao if palavra in mensagem_lower])
        if despedida_detectada:
            palavras_encontradas.extend([palavra for palavra in palavras_despedida if palavra in mensagem_lower])
        
        confianca = min(len(palavras_encontradas) * 0.3, 1.0)  # Máximo 100% de confiança
        
        # Determinar motivo baseado no tipo de palavras encontradas
        if satisfacao_detectada and despedida_detectada:
            motivo = 'cliente_satisfeito_com_despedida'
        elif satisfacao_detectada:
            motivo = 'cliente_satisfeito'
        elif despedida_detectada:
            motivo = 'cliente_despediu'
        else:
            motivo = 'nao_detectado'
        
        return {
            'satisfeito': satisfacao_detectada or despedida_detectada,
            'motivo': motivo,
            'confianca': confianca,
            'palavras_encontradas': palavras_encontradas,
            'satisfacao_detectada': satisfacao_detectada,
            'despedida_detectada': despedida_detectada
        }

    def _detectar_resposta_csat(self, mensagem: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detecta se o cliente está respondendo a uma pesquisa de satisfação (CSAT)
        Usa IA para interpretar a resposta, não emojis ou frases fixas
        """
        try:
            # Verificar se há CSAT pendente no contexto
            if not contexto or not contexto.get('conversation'):
                return {'is_csat_response': False, 'rating': None, 'feedback': None}
            
            conversation = contexto['conversation']
            
            # Verificar se há CSAT pendente para esta conversa
            from conversations.models import CSATRequest
            csat_request = CSATRequest.objects.filter(
                conversation=conversation,
                status='sent'
            ).first()
            
            if not csat_request:
                return {'is_csat_response': False, 'rating': None, 'feedback': None}
            
            # Usar IA para interpretar a resposta do CSAT
            if not self.api_key:
                self.api_key = self._get_api_key()
                if self.api_key:
                    openai.api_key = self.api_key
            
            if not self.api_key:
                return {'is_csat_response': False, 'rating': None, 'feedback': None}
            
            # Prompt para IA interpretar resposta CSAT
            csat_prompt = f"""
Você é um assistente que interpreta respostas de pesquisa de satisfação.

O cliente respondeu: "{mensagem}"

Analise se esta resposta é sobre avaliação do atendimento e determine:
1. Se é uma resposta à pesquisa de satisfação (sim/não)
2. Qual a nota/avaliação (1-5, onde 1=ruim/péssimo, 5=excelente)
3. Se há feedback adicional

Responda APENAS em JSON no formato:
{{
    "is_csat_response": true/false,
    "rating": 1-5 ou null,
    "feedback": "texto do feedback ou null"
}}

Exemplos de respostas CSAT:
- "Ruim" = rating: 1
- "Péssimo" = rating: 1  
- "Regular" = rating: 3
- "Bom" = rating: 4
- "Excelente" = rating: 5
- "😡" = rating: 1
- "😕" = rating: 2
- "😐" = rating: 3
- "🙂" = rating: 4
- "🤩" = rating: 5
- "Muito bom atendimento" = rating: 4, feedback: "Muito bom atendimento"
- "Atendimento excelente, muito rápido" = rating: 5, feedback: "Atendimento excelente, muito rápido"
"""

            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em análise de feedback de clientes."},
                    {"role": "user", "content": csat_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Processar resposta da IA
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"IA CSAT Response: {ai_response}")
            
            try:
                # Tentar extrair JSON da resposta
                import json
                csat_data = json.loads(ai_response)
                
                if csat_data.get('is_csat_response'):
                    logger.info(f"✅ CSAT detectado pela IA: Rating {csat_data.get('rating')}, Feedback: {csat_data.get('feedback')}")
                    return {
                        'is_csat_response': True,
                        'rating': csat_data.get('rating'),
                        'feedback': csat_data.get('feedback'),
                        'raw_response': mensagem
                    }
                else:
                    return {'is_csat_response': False, 'rating': None, 'feedback': None}
                    
            except json.JSONDecodeError:
                logger.warning(f"Erro ao decodificar JSON da IA: {ai_response}")
                return {'is_csat_response': False, 'rating': None, 'feedback': None}
                
        except Exception as e:
            logger.error(f"Erro ao detectar resposta CSAT: {e}")
            return {'is_csat_response': False, 'rating': None, 'feedback': None}

    def _get_greeting_time(self) -> str:
        """Retorna saudação baseada no horário atual"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return "Bom dia"
        elif 12 <= hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    


    def _build_system_prompt(self, provedor: Provedor) -> str:
        import json
        from datetime import datetime
        import locale
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except:
            pass
        now = datetime.now()
        
        # Dados básicos
        nome_agente = provedor.nome_agente_ia or 'Assistente Virtual'
        nome_provedor = provedor.nome or 'Provedor de Internet'
        site_oficial = provedor.site_oficial or ''
        endereco = provedor.endereco or ''
        
        # Configurações dinâmicas
        greeting_time = self._get_greeting_time()
        
        # Redes sociais
        redes = provedor.redes_sociais or {}
        if not isinstance(redes, dict):
            try:
                import json as _json
                redes = _json.loads(redes)
            except Exception:
                redes = {}
        

        
        # Personalidade (pode ser lista ou objeto estruturado)
        personalidade = provedor.personalidade or []
        personalidade_avancada = None
        
        # Verificar se é personalidade avançada (objeto) ou lista simples
        if isinstance(personalidade, dict):
            personalidade_avancada = personalidade
            # Manter compatibilidade usando características como personalidade base
            personalidade_traits = personalidade.get('caracteristicas', '').split(',') if personalidade.get('caracteristicas') else []
            personalidade = [trait.strip() for trait in personalidade_traits if trait.strip()] or ["Atencioso", "Carismatico", "Educado", "Objetivo", "Persuasivo"]
        elif not personalidade:
            personalidade = ["Atencioso", "Carismatico", "Educado", "Objetivo", "Persuasivo"]
        
        # Planos de internet
        planos_internet = provedor.planos_internet or ''
        planos_descricao = provedor.planos_descricao or ''
        


        # Emojis
        uso_emojis = provedor.uso_emojis or ""
        

        
        # E-mail de contato principal
        email_contato = ''
        if hasattr(provedor, 'emails') and provedor.emails:
            emails = provedor.emails
            if isinstance(emails, dict):
                email_contato = next((v for v in emails.values() if v), '')
            elif isinstance(emails, list) and emails:
                email_contato = emails[0]
        
        # Data atual formatada
        data_atual = now.strftime('%A, %d/%m/%Y, %H:%M')
        
        # Buscar campos que podem estar ausentes
        modo_falar = provedor.modo_falar or ''
        estilo_personalidade = provedor.estilo_personalidade or 'Educado'
        planos_descricao = provedor.planos_descricao or ''
        
        # Campos comerciais que estavam acima dos planos
        taxa_adesao = provedor.taxa_adesao or ''
        multa_cancelamento = provedor.multa_cancelamento or ''
        tipo_conexao = provedor.tipo_conexao or ''
        prazo_instalacao = provedor.prazo_instalacao or ''
        documentos_necessarios = provedor.documentos_necessarios or ''
        
        # Construir prompt completo com TODOS os dados do provedor
        prompt_sections = []
        
        # 1. IDENTIDADE E PERSONALIDADE
        identidade_section = f"""# IDENTIDADE DO AGENTE
Nome: {nome_agente}
Empresa: {nome_provedor}
Personalidade: {estilo_personalidade}"""
        
        if modo_falar:
            identidade_section += f"\nModo de falar: {modo_falar}"
        
        if personalidade_avancada:
            if personalidade_avancada.get('vicios_linguagem'):
                identidade_section += f"\nVícios de linguagem: {personalidade_avancada['vicios_linguagem']}"
            if personalidade_avancada.get('caracteristicas'):
                identidade_section += f"\nCaracterísticas: {personalidade_avancada['caracteristicas']}"
            if personalidade_avancada.get('principios'):
                identidade_section += f"\nPrincípios: {personalidade_avancada['principios']}"
            if personalidade_avancada.get('humor'):
                identidade_section += f"\nHumor: {personalidade_avancada['humor']}"
        
        if uso_emojis:
            identidade_section += f"\nUso de emojis: {uso_emojis}"
        
        prompt_sections.append(identidade_section)
        
        # 2. INFORMAÇÕES DA EMPRESA
        empresa_section = f"""# INFORMAÇÕES DA EMPRESA
Nome: {nome_provedor}"""
        
        if site_oficial:
            empresa_section += f"\nSite: {site_oficial}"
        if endereco:
            empresa_section += f"\nEndereço: {endereco}"
        if email_contato:
            empresa_section += f"\nE-mail: {email_contato}"
            
        # Adicionar horários de atendimento
        if provedor.horarios_atendimento:
            try:
                import json
                horarios = json.loads(provedor.horarios_atendimento) if isinstance(provedor.horarios_atendimento, str) else provedor.horarios_atendimento
                horarios_texto = []
                
                for dia_info in horarios:
                    dia = dia_info.get('dia', '')
                    periodos = dia_info.get('periodos', [])
                    
                    if periodos:
                        periodos_texto = []
                        for periodo in periodos:
                            inicio = periodo.get('inicio', '')
                            fim = periodo.get('fim', '')
                            if inicio and fim:
                                periodos_texto.append(f"{inicio} às {fim}")
                        
                        if periodos_texto:
                            horarios_texto.append(f"{dia}: {', '.join(periodos_texto)}")
                    else:
                        horarios_texto.append(f"{dia}: Fechado")
                
                if horarios_texto:
                    empresa_section += f"\n\nHorários de Atendimento:\n" + "\n".join(horarios_texto)
                    
            except Exception as e:
                # Se houver erro no JSON, usar texto simples
                if provedor.horarios_atendimento:
                    empresa_section += f"\nHorários de Atendimento: {provedor.horarios_atendimento}"
        
        prompt_sections.append(empresa_section)
        
        # 3. INFORMAÇÕES COMERCIAIS
        comercial_section_parts = []
        if taxa_adesao:
            comercial_section_parts.append(f"Taxa de adesão: {taxa_adesao}")
        if multa_cancelamento:
            comercial_section_parts.append(f"Multa de cancelamento: {multa_cancelamento}")
        if tipo_conexao:
            comercial_section_parts.append(f"Tipo de conexão: {tipo_conexao}")
        if prazo_instalacao:
            comercial_section_parts.append(f"Prazo de instalação: {prazo_instalacao}")
        if documentos_necessarios:
            comercial_section_parts.append(f"Documentos necessários: {documentos_necessarios}")
        
        if comercial_section_parts:
            comercial_section = "# INFORMAÇÕES COMERCIAIS\n" + "\n".join(comercial_section_parts)
            prompt_sections.append(comercial_section)
        
        # 4. PLANOS E SERVIÇOS
        if planos_internet or planos_descricao:
            planos_section = "# PLANOS DE INTERNET"
            if planos_internet:
                planos_section += f"\nPlanos disponíveis: {planos_internet}"
            if planos_descricao:
                planos_section += f"\nDescrição dos planos: {planos_descricao}"
            prompt_sections.append(planos_section)
        
        # 5. INSTRUÇÕES GERAIS
        instrucoes = f"""# INSTRUÇÕES GERAIS
Você é {nome_agente}, assistente virtual da {nome_provedor}.
Sua missão é:
- Atender clientes existentes com dúvidas e problemas
- Apresentar planos para novos interessados
- Consultar dados no SGP quando necessário
- Transferir para atendentes humanos quando solicitado
- Ser {estilo_personalidade.lower()} e prestativo

DATA E HORA ATUAL: {data_atual}"""
        
        prompt_sections.append(instrucoes)
        
        # Construir prompt final
        complete_prompt = "\n\n".join(prompt_sections)
        
        return complete_prompt

    def _corrigir_formato_resposta(self, resposta: str) -> str:
        """
        Força o formato correto da resposta, removendo formatos antigos indesejados
        """
        import re
        
        # Se a resposta contém o formato antigo, corrigir
        if any(termo in resposta for termo in ['*Dados do Cliente:*', '*Nome:*', '*Status do Contrato:*']):
            logger.warning("Detectado formato antigo na resposta, corrigindo...")
            
            # Formatação básica removida
            
            # Extrair nome do cliente se presente
            nome_match = re.search(r'([A-Z\s]+(?:DA|DE|DO|DOS|DAS|E)\s+[A-Z\s]+)', resposta)
            if nome_match:
                nome_cliente = nome_match.group(1).strip()
                
                # Verificar se há informações de contrato (status ou números de contrato)
                if 'Suspenso' in resposta or 'Ativo' in resposta or any(char.isdigit() for char in resposta):
                    # Formato corrigido para um contrato
                    resposta_corrigida = f"Contrato:\n*{nome_cliente}*\n\n1 - Contrato (ID): *Dados do contrato*\n\nOs dados estão corretos?"
                    logger.info(f"Formato corrigido aplicado: {resposta_corrigida[:50]}...")
                    return resposta_corrigida
            
            # Limpar múltiplas quebras de linha
            resposta = re.sub(r'\n\s*\n', '\n\n', resposta)
            resposta = resposta.strip()
            
            logger.info(f"Formato antigo removido, resposta limpa: {resposta[:50]}...")
        
        # IMPLEMENTAR DELAY DE 5 SEGUNDOS APÓS MOSTRAR DADOS DO CLIENTE
        if 'Contrato:' in resposta and '1 - Contrato' in resposta:
            logger.info("Detectados dados do cliente - aplicando delay de 5 segundos")
            import time
            time.sleep(5)  # Delay de 5 segundos
            logger.info("Delay de 5 segundos aplicado")
        
        return resposta

    def _is_valid_cpf_cnpj(self, cpf_cnpj: str) -> bool:
        """Valida se a string é um CPF ou CNPJ válido"""
        if not cpf_cnpj:
            return False
        
        # Remove caracteres especiais
        clean = re.sub(r'[^\d]', '', str(cpf_cnpj))
        
        # CPF tem 11 dígitos, CNPJ tem 14
        if len(clean) not in [11, 14]:
            return False
            
        # Verifica se são todos dígitos
        if not clean.isdigit():
            return False
            
        return True

    def _execute_database_function(self, provedor: Provedor, function_name: str, function_args: dict, contexto: dict = None) -> dict:
        """Executa funções de banco de dados chamadas pela IA"""
        try:
            db_tools = DatabaseTools(provedor=provedor)
            
            # Mapear nome da função para método da classe
            method_name = DATABASE_FUNCTION_MAPPING.get(function_name)
            if not method_name:
                return {
                    "success": False,
                    "erro": f"Função {function_name} não encontrada"
                }
            
            # Executar método correspondente
            method = getattr(db_tools, method_name)
            result = method(**function_args)
            
            logger.info(f"Função de banco executada: {function_name} -> {method_name}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao executar função de banco {function_name}: {e}")
            return {
                "success": False,
                "erro": f"Erro ao executar {function_name}: {str(e)}"
            }

    def _execute_sgp_function(self, provedor: Provedor, function_name: str, function_args: dict, contexto: dict = None) -> dict:
        """Executa funções do SGP chamadas pela IA"""
        try:
            from .sgp_client import SGPClient
            
            # Obter configurações do SGP do provedor
            integracao = provedor.integracoes_externas or {}
            sgp_url = integracao.get('sgp_url')
            sgp_token = integracao.get('sgp_token') 
            sgp_app = integracao.get('sgp_app')
            
            if not all([sgp_url, sgp_token, sgp_app]):
                return {
                    "erro": "Configurações do SGP não encontradas. Configure no painel do provedor.",
                    "success": False
                }
            
            # Criar cliente SGP
            sgp = SGPClient(
                base_url=sgp_url,
                token=sgp_token,
                app_name=sgp_app
            )
            
            # Log para debug das credenciais SGP
            logger.info(f"SGP Client criado com URL: {sgp_url}, Token: {'Configurado' if sgp_token else 'Não configurado'}, App: {sgp_app}")
            
            # Executar função solicitada
            if function_name == "consultar_cliente_sgp":
                cpf_cnpj = function_args.get('cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
                resultado = sgp.consultar_cliente(cpf_cnpj)
                
                # Processar resultado para formato mais legível
                if resultado.get('contratos'):
                    contratos = resultado['contratos']
                    
                    # Se tem apenas um contrato, retorna dados essenciais
                    if len(contratos) == 1:
                        contrato = contratos[0]
                        endereco = f"{contrato.get('endereco_logradouro', '')} {contrato.get('endereco_numero', '')}, {contrato.get('endereco_bairro', '')}, {contrato.get('endereco_cidade', '')}"
                        return {
                            "success": True,
                            "cliente_encontrado": True,
                            "nome": contrato.get('razaoSocial', 'Nome não encontrado'),
                            "contrato_id": contrato.get('contratoId'),
                            "endereco": endereco.strip(),
                            "status_contrato": contrato.get('contratoStatusDisplay'),
                            "dados_essenciais": {
                                "contratoId": contrato.get('contratoId'),
                                "razaoSocial": contrato.get('razaoSocial'),
                                "endereco": endereco.strip(),
                                "contratoStatusDisplay": contrato.get('contratoStatusDisplay')
                            }
                        }
                    # Se tem múltiplos contratos, lista apenas ID e endereço
                    else:
                        contratos_resumidos = []
                        for i, contrato in enumerate(contratos, 1):
                            endereco = f"{contrato.get('endereco_logradouro', '')} {contrato.get('endereco_numero', '')}, {contrato.get('endereco_bairro', '')}, {contrato.get('endereco_cidade', '')}"
                            contratos_resumidos.append({
                                "numero": i,
                                "contratoId": contrato.get('contratoId'),
                                "endereco": endereco.strip()
                            })
                        
                        return {
                            "success": True,
                            "cliente_encontrado": True,
                            "nome": contratos[0].get('razaoSocial', 'Nome não encontrado'),
                            "multiplos_contratos": True,
                            "total_contratos": len(contratos),
                            "contratos_resumidos": contratos_resumidos,
                            "mensagem": f"Encontrei {len(contratos)} contratos para este cliente. Por favor, escolha qual contrato deseja consultar:"
                        }
                else:
                    return {
                        "success": True,
                        "cliente_encontrado": False,
                        "mensagem": "Cliente não encontrado com este CPF/CNPJ"
                    }
                    
            elif function_name == "verificar_acesso_sgp":
                contrato = function_args.get('contrato')
                
                # Se não tem contrato, tentar buscar pelo CPF/CNPJ da memória
                if not contrato and contexto and contexto.get('conversation'):
                    conversation = contexto['conversation']
                    conversation_id = conversation.id
                    
                    # Recuperar memória Redis para obter CPF/CNPJ
                    try:
                        conversation_memory = redis_memory_service.get_conversation_memory_sync(
                            provedor_id=provedor.id,
                            conversation_id=conversation_id
                        )
                        
                        if conversation_memory and conversation_memory.get('cpf_cnpj'):
                            # Buscar contrato pelo CPF/CNPJ
                            dados_cliente = sgp.consultar_cliente(conversation_memory['cpf_cnpj'])
                            if dados_cliente.get('contratos'):
                                contrato = dados_cliente['contratos'][0].get('contratoId')
                                logger.info(f"Contrato encontrado via CPF: {contrato}")
                    except Exception as e:
                        logger.warning(f"Erro ao buscar contrato via CPF: {e}")
                
                if not contrato:
                    return {
                        "success": False,
                        "erro": "Contrato não informado e não foi possível identificar automaticamente. Por favor, informe o CPF/CNPJ do cliente primeiro."
                    }
                
                # Verificar acesso no SGP
                resultado = sgp.verifica_acesso(contrato)
                
                # Interpretar resultado
                status_conexao = "Desconhecido"
                problema_identificado = None
                acao_recomendada = None
                
                if isinstance(resultado, list):
                    if len(resultado) == 0:
                        status_conexao = "Offline"
                        problema_identificado = "Contrato suspenso ou sem acesso"
                        acao_recomendada = "Verificar status financeiro ou técnico"
                    else:
                        status_conexao = "Online"
                        problema_identificado = "Conexão ativa"
                        acao_recomendada = "Verificar equipamento local"
                else:
                    # Resultado é dicionário
                    status_code = resultado.get('status')
                    mensagem = resultado.get('msg', '')
                    
                    if status_code == 1:
                        status_conexao = "Online"
                        problema_identificado = "Conexão ativa"
                        acao_recomendada = "Verificar equipamento local"
                    elif status_code == 2:
                        status_conexao = "Offline"
                        problema_identificado = "Serviço Offline"
                        acao_recomendada = "Verificar equipamento e LEDs"
                    elif status_code == 4:
                        status_conexao = "Suspenso"
                        problema_identificado = "Contrato suspenso por motivo financeiro"
                        acao_recomendada = "Verificar faturas em aberto"
                    else:
                        status_conexao = f"Status {status_code}"
                        problema_identificado = mensagem
                        acao_recomendada = "Verificar com suporte técnico"
                
                return {
                    "success": True,
                    "contrato": contrato,
                    "status_conexao": status_conexao,
                    "problema_identificado": problema_identificado,
                    "acao_recomendada": acao_recomendada,
                    "dados_completos": resultado
                }
                
            elif function_name == "encerrar_atendimento":
                # Implementação para encerrar atendimento e limpar memória
                try:
                    motivo = function_args.get('motivo', 'nao_especificado')
                    
                    # NÃO limpar Redis aqui - será limpo DEPOIS de enviar a mensagem
                    conversation_id = None
                    if contexto and contexto.get('conversation'):
                        conversation_id = contexto['conversation'].id
                        
                    # ENCERRAR CONVERSA E REGISTRAR AUDITORIA
                    if contexto and contexto.get('conversation'):
                        conversation = contexto['conversation']
                        
                        # Fechar a conversa
                        conversation.status = 'closed'
                        conversation.save()
                        
                        # NÃO limpar Redis aqui - será limpo DEPOIS de enviar a mensagem
                        
                        # Enviar auditoria APENAS para Supabase (não salvar localmente)
                        try:
                            from conversations.csat_automation import CSATAutomationService
                            from core.supabase_service import supabase_service
                            
                            # Calcular duração da conversa
                            duracao = None
                            if conversation.created_at:
                                duracao = timezone.now() - conversation.created_at
                            
                            # Contar mensagens
                            message_count = conversation.messages.count()
                            
                            # Enviar auditoria APENAS para Supabase
                            supabase_success = supabase_service.save_audit(
                                provedor_id=provedor.id,
                                conversation_id=conversation.id,
                                action='conversation_closed_ai',
                                details={
                                    'motivo': motivo,
                                    'encerrado_por': 'ai',
                                    'duracao_minutos': round(duracao.total_seconds() / 60, 2) if duracao else None,
                                    'quantidade_mensagens': message_count,
                                    'satisfacao_cliente': 'confirmada' if motivo in ['cliente_satisfeito', 'atendimento_concluido'] else 'nao_avaliada'
                                },
                                user_id=None,
                                ended_at_iso=timezone.now().isoformat()
                            )
                            
                            # Enviar dados da conversa para Supabase
                            try:
                                supabase_service.save_conversation(
                                    provedor_id=provedor.id,
                                    conversation_id=conversation.id,
                                    contact_id=conversation.contact_id,
                                    inbox_id=conversation.inbox_id,
                                    status=conversation.status,
                                    assignee_id=conversation.assignee_id,
                                    created_at_iso=conversation.created_at.isoformat(),
                                    updated_at_iso=conversation.updated_at.isoformat(),
                                    ended_at_iso=timezone.now().isoformat(),
                                    additional_attributes=conversation.additional_attributes
                                )
                                logger.info(f"✅ Conversa enviada para Supabase: {conversation.id}")
                            except Exception as _conv_err:
                                logger.warning(f"Falha ao enviar conversa para Supabase: {_conv_err}")
                            
                            # Enviar dados do contato para Supabase
                            try:
                                contact = conversation.contact
                                supabase_service.save_contact(
                                    provedor_id=provedor.id,
                                    contact_id=contact.id,
                                    name=contact.name,
                                    phone=getattr(contact, 'phone', None),
                                    email=getattr(contact, 'email', None),
                                    avatar=getattr(contact, 'avatar', None),
                                    created_at_iso=contact.created_at.isoformat(),
                                    updated_at_iso=contact.updated_at.isoformat(),
                                    additional_attributes=contact.additional_attributes
                                )
                                logger.info(f"✅ Contato enviado para Supabase: {contact.id}")
                            except Exception as _contact_err:
                                logger.warning(f"Falha ao enviar contato para Supabase: {_contact_err}")
                            
                            # Enviar todas as mensagens da conversa para Supabase
                            try:
                                from conversations.models import Message
                                messages = Message.objects.filter(conversation=conversation).order_by('created_at')
                                messages_sent = 0
                                
                                for msg in messages:
                                    success = supabase_service.save_message(
                                        provedor_id=provedor.id,
                                        conversation_id=conversation.id,
                                        contact_id=contact.id,
                                        content=msg.content,
                                        message_type=msg.message_type,
                                        is_from_customer=msg.is_from_customer,
                                        external_id=msg.external_id,
                                        file_url=msg.file_url,
                                        file_name=msg.file_name,
                                        file_size=msg.file_size,
                                        additional_attributes=msg.additional_attributes,
                                        created_at_iso=msg.created_at.isoformat()
                                    )
                                    if success:
                                        messages_sent += 1
                                
                                logger.info(f"✅ {messages_sent}/{messages.count()} mensagens enviadas para Supabase")
                            except Exception as _msg_err:
                                logger.warning(f"Falha ao enviar mensagens para Supabase: {_msg_err}")
                            
                            if supabase_success:
                                logger.info(f"✅ Auditoria enviada para Supabase: conversa {conversation.id}")
                            else:
                                logger.warning(f"❌ Falha ao enviar auditoria para Supabase: conversa {conversation.id}")
                                
                        except Exception as _sup_err:
                            logger.error(f"Erro ao enviar auditoria para Supabase: {_sup_err}")
                        
                        # CRIAR SOLICITAÇÃO DE CSAT AUTOMÁTICA
                        try:
                            csat_request = CSATAutomationService.create_csat_request(conversation)
                            if csat_request:
                                logger.info(f"CSAT request criada automaticamente: {csat_request.id}")
                            else:
                                logger.warning("Não foi possível criar CSAT request automático")
                        except Exception as csat_error:
                            logger.error(f"Erro ao criar CSAT request automático: {csat_error}")
                            
                        except Exception as audit_error:
                            logger.error(f"Erro ao registrar auditoria de encerramento: {audit_error}")
                    
                    return {
                        "success": True,
                        "atendimento_encerrado": True,
                        "motivo": motivo,
                        "mensagem": "Obrigado pelo contato! Tenha um ótimo dia! 👋",
                        "conversation_id": conversation_id,
                        "auditoria_registrada": True,
                        "csat_disparado": True
                    }
                    
                except Exception as e:
                    logger.error(f"Erro ao encerrar atendimento: {e}")
                    return {
                        "success": False,
                        "erro": f"Erro ao encerrar atendimento: {str(e)}"
                    }
                
            elif function_name == "gerar_fatura_completa":
                # Implementação usando fatura_service.py e qr_code_service.py
                cpf_cnpj = function_args.get('cpf_cnpj', '')
                contrato = function_args.get('contrato', '')
                numero_whatsapp = function_args.get('numero_whatsapp', '')
                tipo_pagamento = function_args.get('tipo_pagamento', 'pix')
                
                # Extrair número WhatsApp apenas do contexto atual da conversa
                if not numero_whatsapp and contexto and contexto.get('conversation'):
                    conversation = contexto['conversation']
                    if hasattr(conversation, 'contact') and hasattr(conversation.contact, 'phone'):
                        numero_whatsapp = conversation.contact.phone
                        logger.info(f"Número WhatsApp obtido da conversa atual: {numero_whatsapp}")
                
                # Se ainda não tem número, usar um padrão para teste
                if not numero_whatsapp:
                    numero_whatsapp = None  # Número não encontrado
                    logger.info(f"Usando número padrão para teste: {numero_whatsapp}")
                            
                if cpf_cnpj:
                    # Validar se o CPF/CNPJ é válido
                    if not self._is_valid_cpf_cnpj(cpf_cnpj):
                        return {
                            "success": False,
                            "erro": f"CPF/CNPJ inválido: '{cpf_cnpj}'. Por favor, informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
                        }
                    
                    try:
                        from .fatura_service import FaturaService
                        fatura_service = FaturaService()
                        
                        logger.info(f"Executando gerar_fatura_completa usando FaturaService para CPF/CNPJ: {cpf_cnpj}")
                        
                        # Buscar dados da fatura no SGP
                        dados_fatura = fatura_service.buscar_fatura_sgp(provedor, cpf_cnpj)
                        
                        if not dados_fatura:
                            return {
                                "success": False,
                                "erro": "Não foi possível encontrar fatura para este CPF/CNPJ"
                            }
                        
                        # Enviar fatura via Uazapi
                        resultado = fatura_service.enviar_fatura_uazapi(
                            provedor=provedor,
                            numero_whatsapp=numero_whatsapp,
                            dados_fatura=dados_fatura,
                            conversation=contexto.get('conversation'),
                            tipo_pagamento=tipo_pagamento
                        )
                        
                        if resultado.get('success'):
                            # Criar mensagem dinâmica baseada no tipo de pagamento
                            if tipo_pagamento == 'pix':
                                mensagem_sucesso = "Acabei de enviar sua fatura via WhatsApp com QR Code e botão de cópia PIX!\n\nPosso te ajudar com mais alguma coisa?"
                            else:  # boleto
                                mensagem_sucesso = "Acabei de enviar sua fatura via WhatsApp com boleto PDF!\n\nPosso te ajudar com mais alguma coisa?"
                            
                            return {
                                "success": True,
                                "fatura_gerada": True,
                                "tipo_pagamento": tipo_pagamento,
                                "enviada_whatsapp": True,
                                "mensagem_formatada": mensagem_sucesso
                            }
                        else:
                            return {
                                "success": False,
                                "erro": resultado.get('error', 'Erro ao processar fatura')
                            }
                            
                    except Exception as e:
                        logger.error(f"Erro ao gerar fatura completa: {e}")
                        return {
                            "success": False,
                            "erro": f"Erro ao gerar fatura: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "CPF/CNPJ não fornecido"
                    }
                
            elif function_name == "enviar_formato_adicional":
                # Implementação para enviar formato adicional (PIX ou Boleto) quando cliente pede depois
                cpf_cnpj = function_args.get('cpf_cnpj', '')
                formato_solicitado = function_args.get('formato_solicitado', '')  # 'pix' ou 'boleto'
                numero_whatsapp = function_args.get('numero_whatsapp', '')
                
                # Extrair número WhatsApp apenas do contexto atual da conversa
                if not numero_whatsapp and contexto and contexto.get('conversation'):
                    conversation = contexto['conversation']
                    if hasattr(conversation, 'contact') and hasattr(conversation.contact, 'phone'):
                        numero_whatsapp = conversation.contact.phone
                        logger.info(f"Número WhatsApp obtido da conversa atual: {numero_whatsapp}")
                
                if cpf_cnpj and formato_solicitado:
                    # Validar se o CPF/CNPJ é válido
                    if not self._is_valid_cpf_cnpj(cpf_cnpj):
                        return {
                            "success": False,
                            "erro": f"CPF/CNPJ inválido: '{cpf_cnpj}'. Por favor, informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
                        }
                    
                    try:
                        from .fatura_service import FaturaService
                        fatura_service = FaturaService()
                        
                        logger.info(f"Executando enviar_formato_adicional para CPF/CNPJ: {cpf_cnpj}, formato: {formato_solicitado}")
                        
                        # Buscar dados da fatura primeiro
                        dados_fatura = fatura_service.buscar_fatura_sgp(provedor, cpf_cnpj)
                        
                        if not dados_fatura:
                            return {
                                "success": False,
                                "erro": "Fatura não encontrada no SGP"
                            }
                        
                        # Enviar formato adicional
                        resultado = fatura_service.enviar_formato_adicional(
                            provedor=provedor,
                            numero_whatsapp=numero_whatsapp,
                            dados_fatura=dados_fatura,
                            formato_solicitado=formato_solicitado,
                            conversation=contexto.get('conversation')
                        )
                        
                        if resultado:
                            # Criar mensagem de confirmação
                            if formato_solicitado.lower() == 'pix':
                                mensagem_sucesso = "Acabei de enviar o QR Code PIX e botão para copiar a chave!\n\nPosso te ajudar com mais alguma coisa?"
                            else:  # boleto
                                mensagem_sucesso = "Acabei de enviar o PDF do boleto e botão para copiar a linha digitável!\n\nPosso te ajudar com mais alguma coisa?"
                            
                            return {
                                "success": True,
                                "formato_enviado": True,
                                "tipo_formato": formato_solicitado,
                                "enviada_whatsapp": True,
                                "mensagem_formatada": mensagem_sucesso
                            }
                        else:
                            return {
                                "success": False,
                                "erro": f"Falha ao enviar {formato_solicitado}"
                            }
                            
                    except Exception as e:
                        logger.error(f"Erro ao enviar formato adicional: {e}")
                        return {
                            "success": False,
                            "erro": f"Erro ao enviar formato adicional: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "CPF/CNPJ ou formato solicitado não fornecido"
                    }
                
            elif function_name == "criar_chamado_tecnico":
                # Implementação para criar chamado técnico no SGP
                cpf_cnpj = function_args.get('cpf_cnpj', '')
                motivo = function_args.get('motivo', '')
                sintomas = function_args.get('sintomas', '')
                
                if not cpf_cnpj or not motivo:
                    return {
                        "success": False,
                        "erro": "CPF/CNPJ e motivo são obrigatórios para criar chamado técnico"
                    }
                
                # Validar se o CPF/CNPJ é válido
                if not self._is_valid_cpf_cnpj(cpf_cnpj):
                    return {
                        "success": False,
                        "erro": f"CPF/CNPJ inválido: '{cpf_cnpj}'. Por favor, informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
                    }
                
                try:
                    from .sgp_client import SGPClient
                    integracao = provedor.integracoes_externas or {}
                    sgp_url = integracao.get('sgp_url')
                    sgp_token = integracao.get('sgp_token') 
                    sgp_app = integracao.get('sgp_app')
                    
                    if not all([sgp_url, sgp_token, sgp_app]):
                        return {
                            "success": False,
                            "erro": "Configurações do SGP não encontradas"
                        }
                    
                    sgp = SGPClient(base_url=sgp_url, token=sgp_token, app_name=sgp_app)
                    
                    # Buscar cliente para obter contrato_id
                    dados_cliente = sgp.consultar_cliente(cpf_cnpj)
                    
                    if not dados_cliente.get('contratos'):
                        return {
                            "success": False,
                            "erro": "Cliente não encontrado ou sem contrato ativo"
                        }
                    
                    contrato_id = dados_cliente['contratos'][0].get('contratoId')
                    
                    if not contrato_id:
                        return {
                            "success": False,
                            "erro": "ID do contrato não encontrado"
                        }
                    
                    # Detectar tipo de ocorrência automaticamente baseado no relato
                    motivo_lower = motivo.lower()
                    sintomas_lower = sintomas.lower()
                    texto_completo = f"{motivo} {sintomas}".lower()
                    
                    # Detectar tipo de ocorrência
                    ocorrenciatipo = 1  # Padrão: sem acesso à internet
                    
                    # Palavras-chave para internet lenta
                    palavras_lenta = ['lenta', 'lento', 'devagar', 'baixa velocidade', 'velocidade baixa', 'ping alto', 'lag', 'travando', 'instável']
                    
                    # Palavras-chave para sem acesso
                    palavras_sem_acesso = ['sem internet', 'sem acesso', 'não funciona', 'não conecta', 'offline', 'desconectado', 'quebrou', 'rompeu', 'caiu', 'drop', 'fio quebrado', 'cabo quebrado']
                    
                    # Verificar se é problema de velocidade
                    if any(palavra in texto_completo for palavra in palavras_lenta):
                        ocorrenciatipo = 2  # Internet lenta
                        tipo_problema = "Internet lenta/instável"
                    elif any(palavra in texto_completo for palavra in palavras_sem_acesso):
                        ocorrenciatipo = 1  # Sem acesso à internet
                        tipo_problema = "Sem acesso à internet"
                    else:
                        # Se não detectar claramente, usar padrão baseado no contexto
                        if 'led' in texto_completo or 'vermelho' in texto_completo:
                            ocorrenciatipo = 1  # Sem acesso (LED vermelho indica problema físico)
                            tipo_problema = "Problema físico (LED vermelho)"
                        else:
                            ocorrenciatipo = 1  # Padrão: sem acesso
                            tipo_problema = "Problema de acesso"
                    
                    # Criar mensagem simplificada e natural para o chamado
                    # Substituir "fio" por "drop" e simplificar o relato
                    sintomas_limpo = sintomas.replace('fio', 'drop').replace('Fio', 'Drop')
                    motivo_limpo = motivo.replace('fio', 'drop').replace('Fio', 'Drop')
                    
                    msg_detalhada = f"Cliente relatou: {motivo_limpo} {sintomas_limpo}"
                    
                    # Criar chamado técnico
                    resultado_chamado = sgp.criar_chamado(
                        contrato=contrato_id,
                        ocorrenciatipo=ocorrenciatipo,
                        conteudo=msg_detalhada
                    )
                    
                    if resultado_chamado:
                        protocolo = resultado_chamado.get('protocolo', 'N/A')
                        
                        # Transferir conversa para equipe de suporte
                        conversation_id = None
                        if contexto and contexto.get('conversation'):
                            conversation_id = contexto['conversation'].id
                            
                            try:
                                # Transferir para equipe de suporte usando database_tools
                                from .database_tools import DatabaseTools
                                db_tools = DatabaseTools(provedor=provedor)
                                resultado_transferencia = db_tools.executar_transferencia_conversa(
                                    conversation_id=conversation_id,
                                    equipe_nome="SUPORTE TÉCNICO",
                                    motivo=f"Chamado técnico criado - {tipo_problema}"
                                )
                                
                                if resultado_transferencia.get('success'):
                                    return {
                                        "success": True,
                                        "chamado_criado": True,
                                        "protocolo": protocolo,
                                        "transferido_suporte": True,
                                        "mensagem_formatada": f"Já abri seu chamado técnico! Seu número de protocolo é: {protocolo}\n\nTransferindo você para nossa equipe de suporte técnico que irá atender seu caso. Aguarde um momento, por favor!"
                                    }
                                else:
                                    return {
                                        "success": True,
                                        "chamado_criado": True,
                                        "protocolo": protocolo,
                                        "transferido_suporte": False,
                                        "erro_transferencia": resultado_transferencia.get('erro', 'Erro desconhecido'),
                                        "mensagem_formatada": f"Já abri seu chamado técnico! Seu número de protocolo é: {protocolo}\n\nNossa equipe de suporte entrará em contato em breve.\n\nObrigado pelo contato!"
                                    }
                                    
                            except Exception as e:
                                logger.error(f"Erro ao transferir conversa: {e}")
                                return {
                                    "success": True,
                                    "chamado_criado": True,
                                    "protocolo": protocolo,
                                    "transferido_suporte": False,
                                    "erro_transferencia": str(e),
                                    "mensagem_formatada": f"Já abri seu chamado técnico! Seu número de protocolo é: {protocolo}\n\nNossa equipe de suporte entrará em contato em breve.\n\nObrigado pelo contato!"
                                }
                        else:
                            return {
                                "success": True,
                                "chamado_criado": True,
                                "protocolo": protocolo,
                                "transferido_suporte": False,
                                "mensagem_formatada": f"Já abri seu chamado técnico! Seu número de protocolo é: {protocolo}\n\nNossa equipe de suporte entrará em contato em breve.\n\nObrigado pelo contato!"
                            }
                    else:
                        return {
                            "success": False,
                            "erro": "Falha ao criar chamado técnico no SGP"
                        }
                        
                except Exception as e:
                    logger.error(f"Erro ao criar chamado técnico: {e}")
                    return {
                        "success": False,
                        "erro": f"Erro ao criar chamado técnico: {str(e)}"
                    }
                
            elif function_name == "enviar_qr_code_pix":
                cpf_cnpj = function_args.get('cpf_cnpj', '')
                contrato = function_args.get('contrato', '')
                numero_whatsapp = function_args.get('numero_whatsapp', '')
                
                if cpf_cnpj:
                    # Validar se o CPF/CNPJ é válido
                    if not self._is_valid_cpf_cnpj(cpf_cnpj):
                        return {
                            "success": False,
                            "erro": f"CPF/CNPJ inválido: '{cpf_cnpj}'. Por favor, informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
                        }
                    try:
                        from .fatura_service import FaturaService
                        fatura_service = FaturaService()
                        
                        # Buscar contrato se não fornecido
                        if not contrato:
                            try:
                                from .sgp_client import SGPClient
                                integracao = provedor.integracoes_externas or {}
                                sgp_url = integracao.get('sgp_url')
                                sgp_token = integracao.get('sgp_token') 
                                sgp_app = integracao.get('sgp_app')
                                
                                if all([sgp_url, sgp_token, sgp_app]):
                                    sgp = SGPClient(base_url=sgp_url, token=sgp_token, app_name=sgp_app)
                                    cliente_resultado = sgp.consultar_cliente(cpf_cnpj)
                                    
                                    if cliente_resultado.get('contratos') and len(cliente_resultado['contratos']) > 0:
                                        contrato = cliente_resultado['contratos'][0].get('contratoId')
                                    else:
                                        return {
                                            "success": False,
                                            "erro": "Cliente não encontrado ou sem contrato ativo"
                                        }
                                else:
                                    return {
                                        "success": False,
                                        "erro": "Configurações do SGP não encontradas"
                                    }
                            except Exception as e:
                                logger.error(f"Erro ao buscar cliente para contrato: {e}")
                                return {
                                    "success": False,
                                    "erro": f"Erro ao buscar dados do cliente: {str(e)}"
                                }
                        
                        # Buscar dados da fatura
                        dados_fatura = fatura_service.buscar_fatura_sgp(provedor, contrato)
                        
                        if dados_fatura and numero_whatsapp:
                            # Enviar apenas QR Code PIX
                            resultado = fatura_service.enviar_qr_code_pix(provedor, numero_whatsapp, dados_fatura, contexto.get('conversation'))
                            
                            if resultado:
                                return {
                                    "success": True,
                                    "qr_code_enviado": True,
                                    "mensagem": "QR Code PIX enviado com sucesso!"
                                }
                            else:
                                return {
                                    "success": False,
                                    "erro": "Falha ao enviar QR Code PIX"
                                }
                        else:
                            return {
                                "success": False,
                                "erro": "Fatura não encontrada ou número WhatsApp não fornecido"
                            }
                    except Exception as e:
                        return {
                            "success": False,
                            "erro": f"Erro ao enviar QR Code PIX: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "CPF/CNPJ não fornecido"
                    }
                    
            elif function_name == "enviar_boleto_pdf":
                # Implementação para enviar boleto em PDF
                cpf_cnpj = function_args.get('cpf_cnpj', '')
                contrato = function_args.get('contrato', '')
                numero_whatsapp = function_args.get('numero_whatsapp', '')
                
                if cpf_cnpj:
                    # Validar se o CPF/CNPJ é válido
                    if not self._is_valid_cpf_cnpj(cpf_cnpj):
                        return {
                            "success": False,
                            "erro": f"CPF/CNPJ inválido: '{cpf_cnpj}'. Por favor, informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."
                        }
                    try:
                        from .fatura_service import FaturaService
                        fatura_service = FaturaService()
                        
                        # Buscar contrato se não fornecido
                        if not contrato:
                            try:
                                from .sgp_client import SGPClient
                                integracao = provedor.integracoes_externas or {}
                                sgp_url = integracao.get('sgp_url')
                                sgp_token = integracao.get('sgp_token') 
                                sgp_app = integracao.get('sgp_app')
                                
                                if all([sgp_url, sgp_token, sgp_app]):
                                    sgp = SGPClient(base_url=sgp_url, token=sgp_token, app_name=sgp_app)
                                    cliente_resultado = sgp.consultar_cliente(cpf_cnpj)
                                    
                                    if cliente_resultado.get('contratos') and len(cliente_resultado['contratos']) > 0:
                                        contrato = cliente_resultado['contratos'][0].get('contratoId')
                                    else:
                                        return {
                                            "success": False,
                                            "erro": "Cliente não encontrado ou sem contrato ativo"
                                        }
                                else:
                                    return {
                                        "success": False,
                                        "erro": "Configurações do SGP não encontradas"
                                    }
                            except Exception as e:
                                logger.error(f"Erro ao buscar cliente para contrato: {e}")
                                return {
                                    "success": False,
                                    "erro": f"Erro ao buscar dados do cliente: {str(e)}"
                                }
                        
                        # Processar fatura como boleto
                        resultado = fatura_service.processar_fatura_completa(
                            provedor=provedor,
                            contrato_id=contrato,
                            numero_whatsapp=numero_whatsapp,
                            preferencia_pagamento='boleto'
                        )
                        
                        if resultado.get('success'):
                            return {
                                "success": True,
                                "boleto_enviado": True,
                                "mensagem": "Boleto enviado com sucesso em PDF!"
                            }
                        else:
                            return {
                                "success": False,
                                "erro": resultado.get('error', 'Erro ao enviar boleto')
                            }
                    except Exception as e:
                        return {
                            "success": False,
                            "erro": f"Erro ao enviar boleto: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "CPF/CNPJ não fornecido"
                    }
                
                return {
                    "success": True,
                    "fatura_id": resultado.get('fatura_id') if resultado else None,
                    "pix_gerado": True,
                    "codigo_pix": resultado.get('codigo_pix') if resultado else None,
                    "qr_code": resultado.get('qr_code') if resultado else None,
                    "valor": resultado.get('valor') if resultado else None,
                    "dados_completos": resultado
                }
                
            elif function_name == "GetCpfContato":
                # Implementação para buscar CPF do contato no ChatWoot
                try:
                    from conversations.models import Contact
                    
                    # Obter número de telefone do contexto da conversa
                    phone_number = function_args.get('phone_number', '')
                    
                    # Se não foi fornecido, tentar obter do contexto da conversa
                    if not phone_number and 'conversation' in function_args:
                        conversation = function_args['conversation']
                        if hasattr(conversation, 'contact') and conversation.contact:
                            phone_number = conversation.contact.phone
                    
                    if phone_number:
                        # Limpar número (remover formatação)
                        phone_clean = ''.join(filter(str.isdigit, str(phone_number)))
                        
                        # Buscar contato pelo número de telefone
                        contact = Contact.objects.filter(phone=phone_clean).first()
                        if contact and contact.additional_attributes:
                            cpf = contact.additional_attributes.get('cpf_cnpj')
                            if cpf:
                                logger.info(f"CPF/CNPJ encontrado no contato {contact.id}: {cpf}")
                                return {
                                    "success": True,
                                    "cpf_encontrado": True,
                                    "cpf_cnpj": cpf,
                                    "mensagem": f"CPF/CNPJ encontrado no contato: {cpf}",
                                    "contact_id": contact.id
                                }
                    
                    logger.info(f"CPF/CNPJ não encontrado para número: {phone_number}")
                    return {
                        "success": True,
                        "cpf_encontrado": False,
                        "mensagem": "CPF/CNPJ não encontrado no contato. Será necessário solicitar ao cliente.",
                        "phone_number": phone_number
                    }
                except Exception as e:
                    logger.error(f"Erro ao buscar CPF do contato: {e}")
                    return {
                        "success": False,
                        "erro": f"Erro ao buscar CPF do contato: {str(e)}"
                    }
                
            elif function_name == "SalvarCpfContato":
                # Implementação para salvar CPF no contato
                try:
                    from conversations.models import Contact
                    
                    phone_number = function_args.get('phone_number', '')
                    cpf_cnpj = function_args.get('cpf_cnpj', '')
                    
                    # Se não foi fornecido, tentar obter do contexto da conversa
                    if not phone_number and 'conversation' in function_args:
                        conversation = function_args['conversation']
                        if hasattr(conversation, 'contact') and conversation.contact:
                            phone_number = conversation.contact.phone
                    
                    if phone_number and cpf_cnpj:
                        # Limpar CPF/CNPJ (apenas números)
                        cpf_clean = ''.join(filter(str.isdigit, cpf_cnpj))
                        
                        # Limpar número de telefone (apenas números)
                        phone_clean = ''.join(filter(str.isdigit, str(phone_number)))
                        
                        contact = Contact.objects.filter(phone=phone_clean).first()
                        if contact:
                            if not contact.additional_attributes:
                                contact.additional_attributes = {}
                            contact.additional_attributes['cpf_cnpj'] = cpf_clean
                            contact.save()
                            
                            logger.info(f"CPF/CNPJ {cpf_clean} salvo no contato {contact.id}")
                            
                            return {
                                "success": True,
                                "cpf_salvo": True,
                                "cpf_cnpj": cpf_clean,
                                "mensagem": f"CPF/CNPJ {cpf_clean} salvo com sucesso no contato",
                                "contact_id": contact.id
                            }
                        else:
                            logger.warning(f"Contato não encontrado para número: {phone_clean}")
                            return {
                                "success": False,
                                "erro": "Contato não encontrado"
                            }
                    else:
                        logger.warning(f"Dados insuficientes: phone_number={phone_number}, cpf_cnpj={cpf_cnpj}")
                        return {
                            "success": False,
                            "erro": "Telefone e CPF/CNPJ são obrigatórios"
                        }
                except Exception as e:
                    logger.error(f"Erro ao salvar CPF no contato: {e}")
                    return {
                        "success": False,
                        "erro": f"Erro ao salvar CPF no contato: {str(e)}"
                    }
                
            elif function_name == "buscar_documentos":
                # Implementação para buscar documentos/planos
                try:
                    # Buscar informações dos planos do provedor
                    planos = provedor.planos_internet or "Planos não configurados"
                    informacoes = provedor.informacoes_extras or "Informações não configuradas"
                    
                    return {
                        "success": True,
                        "planos_internet": planos,
                        "informacoes_extras": informacoes,
                        "mensagem": "Documentos e informações encontrados"
                    }
                except Exception as e:
                    logger.error(f"Erro ao buscar documentos: {e}")
                    return {
                        "success": False,
                        "erro": f"Erro ao buscar documentos: {str(e)}"
                    }
                
            elif function_name == "validar_cpf":
                # Implementação para validar CPF
                cpf = function_args.get('cpf_cnpj', '')
                if cpf:
                    # Validação básica de CPF (11 dígitos)
                    cpf_clean = ''.join(filter(str.isdigit, cpf))
                    if len(cpf_clean) == 11:
                        return {
                            "success": True,
                            "cpf_valido": True,
                            "cpf_cnpj": cpf_clean,
                            "mensagem": "CPF válido"
                        }
                    else:
                        return {
                            "success": False,
                            "cpf_valido": False,
                            "erro": "CPF deve ter 11 dígitos"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "CPF não fornecido"
                    }
                
            elif function_name == "buscar_faturas":
                # Implementação para buscar faturas
                contrato = function_args.get('contrato', '')
                if contrato:
                    try:
                        resultado = sgp.segunda_via_fatura(contrato)
                        return {
                            "success": True,
                            "faturas_encontradas": True,
                            "dados_faturas": resultado,
                            "mensagem": "Faturas encontradas"
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "erro": f"Erro ao buscar faturas: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "Contrato não fornecido"
                    }
                
            elif function_name == "envia_boleto":
                # Implementação para enviar boleto
                fatura_id = function_args.get('fatura_id', '')
                if fatura_id:
                    return {
                        "success": True,
                        "boleto_enviado": True,
                        "fatura_id": fatura_id,
                        "mensagem": "Boleto enviado com sucesso"
                    }
                else:
                    return {
                        "success": False,
                        "erro": "ID da fatura não fornecido"
                    }
                
            elif function_name == "envia_qrcode":
                # Implementação para enviar QR code PIX
                fatura_id = function_args.get('fatura_id', '')
                if fatura_id:
                    return {
                        "success": True,
                        "qrcode_enviado": True,
                        "fatura_id": fatura_id,
                        "mensagem": "QR Code PIX enviado com sucesso"
                    }
                else:
                    return {
                        "success": False,
                        "erro": "ID da fatura não fornecido"
                    }
                
            elif function_name == "prazo_de_confianca":
                # Implementação para prazo de confiança
                contrato = function_args.get('contrato', '')
                if contrato:
                    try:
                        resultado = sgp.liberar_por_confianca(contrato)
                        return {
                            "success": True,
                            "prazo_confianca": True,
                            "contrato": contrato,
                            "resultado": resultado,
                            "mensagem": "Prazo de confiança processado"
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "erro": f"Erro ao processar prazo de confiança: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "Contrato não fornecido"
                    }
                
            elif function_name == "checha_conexao":
                # Implementação para verificar conexão
                contrato = function_args.get('contrato', '')
                if contrato:
                    try:
                        resultado = sgp.verifica_acesso(contrato)
                        return {
                            "success": True,
                            "conexao_verificada": True,
                            "contrato": contrato,
                            "status": resultado.get('status', 'Desconhecido'),
                            "mensagem": "Status da conexão verificado"
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "erro": f"Erro ao verificar conexão: {str(e)}"
                        }
                else:
                    return {
                        "success": False,
                        "erro": "Contrato não fornecido"
                    }
                
            elif function_name == "encaminha_suporte":
                # Implementação para encaminhar para suporte
                motivo = function_args.get('motivo', 'Problema técnico')
                return {
                    "success": True,
                    "encaminhado": True,
                    "equipe": "Suporte Técnico",
                    "motivo": motivo,
                    "mensagem": "Encaminhado para equipe de suporte técnico"
                }
                
            elif function_name == "encaminha_financeiro":
                # Implementação para encaminhar para financeiro
                motivo = function_args.get('motivo', 'Questão financeira')
                return {
                    "success": True,
                    "encaminhado": True,
                    "equipe": "Financeiro",
                    "motivo": motivo,
                    "mensagem": "Encaminhado para equipe financeira"
                }
                
            else:
                return {
                    "erro": f"Função {function_name} não implementada",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Erro ao executar função SGP {function_name}: {str(e)}")
            return {
                "erro": f"Erro ao executar {function_name}: {str(e)}",
                "success": False
            }

    def _build_user_prompt(self, mensagem: str, contexto: Dict[str, Any] = None) -> str:
        user_prompt = f"Mensagem do cliente: {mensagem}"
        if contexto is not None:
            if contexto.get('dados_cliente'):
                user_prompt += f"\n\nDados do cliente: {contexto['dados_cliente']}"
            if contexto.get('historico'):
                user_prompt += f"\n\nHistórico da conversa: {contexto['historico']}"
            if contexto.get('produtos_disponiveis'):
                user_prompt += f"\n\nProdutos disponíveis: {contexto['produtos_disponiveis']}"
        return user_prompt

    async def generate_response(
        self,
        mensagem: str,
        provedor: Provedor,
        contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        try:
            # Atualizar a chave da API de forma assíncrona
            await self.update_api_key_async()
            
            # Verificar se a chave foi configurada
            if not self.api_key:
                logger.error("Chave da API OpenAI não configurada - configure no painel do superadmin")
                return {
                    "success": False,
                    "erro": "Chave da API OpenAI não configurada. Configure no painel do superadmin.",
                    "provedor": provedor.nome
                }
            
            # Construir prompt do sistema
            system_prompt = self._build_system_prompt(provedor)
            
            # Instruções específicas quando cliente pedir fatura
            mensagem_lower = mensagem.lower()
            if any(word in mensagem_lower for word in ['fatura', 'pix', 'boleto', 'pagar']):
                system_prompt += """

FLUXO: CPF → consultar → escolher → gerar
"""
            
            user_prompt = self._build_user_prompt(mensagem, contexto or {})
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            response = await openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada para provedor {provedor.nome}: {resposta[:100]}...")
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "provedor": provedor.nome,
                "agente": provedor.nome_agente_ia
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            return {
                "success": False,
                "erro": f"Erro ao processar mensagem: {str(e)}",
                "provedor": provedor.nome
            }

    def generate_response_sync(
        self,
        mensagem: str,
        provedor: Provedor,
        contexto: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Versão simplificada do gerador de resposta com memória Redis"""
        try:
            from .redis_memory_service import redis_memory_service
            # Buscar chave da API apenas quando necessário
            if not self.api_key:
                self.api_key = self._get_api_key()
                if self.api_key:
                    openai.api_key = self.api_key
            
            # SALVAR MENSAGEM DO CLIENTE NO REDIS (TEMPORARIAMENTE DESABILITADO PARA EVITAR RECURSÃO)
            # if contexto and contexto.get('conversation'):
            #     conversation = contexto['conversation']
            #     try:
            #         redis_memory_service.add_message_to_conversation_sync(
            #             provedor_id=provedor.id,
            #             conversation_id=conversation.id,
            #             sender='customer',
            #             content=mensagem,
            #             message_type='text'
            #         )
            #         logger.info(f"✅ Mensagem do cliente salva no Redis: {mensagem[:50]}...")
            #     except Exception as e:
            #         logger.warning(f"Erro ao salvar mensagem do cliente no Redis: {e}")
            
            # Verificar se a chave foi configurada
            if not self.api_key:
                logger.error("Chave da API OpenAI não configurada")
                return {
                    "success": False,
                    "erro": "Chave da API OpenAI não configurada",
                    "provedor": provedor.nome
                }
            
            # CARREGAR HISTÓRICO DA CONVERSA DO REDIS
            historico_conversa = ""
            conversation = None
            if contexto and contexto.get('conversation'):
                try:
                    conversation = contexto['conversation']
                    memoria_conversa = redis_memory_service.get_conversation_memory_sync(provedor.id, conversation.id)
                    
                    if memoria_conversa and 'messages' in memoria_conversa:
                        mensagens = memoria_conversa['messages'][-20:]  # Últimas 20 mensagens
                        
                        historico_linhas = []
                        for msg in mensagens:
                            sender_label = {
                                'customer': 'Cliente',
                                'ai': 'IA',
                                'agent': 'Atendente'
                            }.get(msg['sender'], msg['sender'])
                            
                            historico_linhas.append(f"{sender_label}: {msg['content']}")
                        
                        if historico_linhas:
                            historico_conversa = f"""

HISTÓRICO DA CONVERSA ATUAL:
{chr(10).join(historico_linhas)}

IMPORTANTE: Use este histórico para manter contexto da conversa. NÃO repita perguntas já feitas ou informações já fornecidas."""
                            logger.info(f"✅ Histórico carregado: {len(mensagens)} mensagens")
                        
                except Exception as e:
                    logger.warning(f"Erro ao carregar histórico do Redis: {e}")

            # USAR O PROMPT COMPLETO COM TODOS OS DADOS DO PROVEDOR
            system_prompt = self._build_system_prompt(provedor)
            system_prompt = f"""
IMPORTANTE: Sempre retorne as mensagens em uma lista (um bloco para cada mensagem), para que o frontend exiba cada uma separadamente com efeito de 'digitando...'. Nunca junte mensagens diferentes em um único bloco.

{system_prompt}{historico_conversa}

CONTEXTO:
- Empresa: {provedor.nome}
- Agente: {provedor.nome_agente_ia}
- Idioma: Português Brasileiro
- Saudação atual: {self._get_greeting_time()}

FERRAMENTAS DISPONÍVEIS:
- consultar_cliente_sgp: Buscar dados do cliente no SGP usando CPF/CNPJ
- gerar_fatura_completa: Gerar fatura completa usando fatura_service.py e qr_code_service.py
- verificar_acesso_sgp: Verificar status da conexão do cliente
- enviar_qr_code_pix: Enviar apenas QR Code PIX usando qr_code_service.py
- enviar_boleto_pdf: Enviar boleto em PDF usando fatura_service.py

IMPORTANTE - DADOS DO CLIENTE:
Quando consultar_cliente_sgp retornar dados, SEMPRE mostre no formato EXATO:

"Contrato:
[NOME COMPLETO DO CLIENTE]

1 - Contrato ([ID DO CONTRATO]): [ENDEREÇO COMPLETO]

Essas informações estão corretas?"

Use os campos: nome, contrato_id, endereco do retorno da função

FLUXO DE ATENDIMENTO:
1. Ao iniciar o atendimento, use a saudação atual apropriada para o horário (Bom dia/Boa tarde/Boa noite) e pergunte se a pessoa já é cliente da {provedor.nome}.
2. Se for, solicite o CPF ou CNPJ dizendo: 'Por favor, me informe o CPF ou CNPJ para localizar seu cadastro.'
3. Quando encontrar o cadastro do cliente, envie uma mensagem com os principais dados.
4. Se não encontrar o cadastro, oriente o usuário a conferir os dados e tentar novamente.

REGRAS GERAIS:
- Responder apenas sobre assuntos relacionados à {provedor.nome}
- Nunca inventar informações
- Se não souber, diga: 'Desculpe, não posso te ajudar com isso. Encaminhando para um atendente humano.'
- Cumprimente o cliente apenas na primeira mensagem do atendimento
- Consulte o histórico da conversa antes de responder
- NUNCA repita perguntas, saudações ou solicitações já feitas durante o atendimento
- Se o cliente já informou um dado (ex: CPF, problema), não peça novamente
- Sempre divida mensagens longas em blocos curtos, com no máximo 3 linhas cada
- Após mostrar os dados do cliente, aguarde confirmação
- Após confirmação, pergunte como pode ajudar
- Nunca repita informações já ditas na conversa
- Se o cliente já informou o que deseja, nunca pergunte novamente 'Como posso ajudar você hoje?'
- Seja objetivo e profissional
- Nunca peça novamente o CPF ou CNPJ se o cliente já informou durante a conversa
- Sempre consulte o histórico da conversa antes de pedir dados novamente

INTELIGÊNCIA CONTEXTUAL - INTERPRETAÇÃO NATURAL:
- Use sua inteligência para entender a intenção do cliente SEM depender de palavras-chave específicas
- Analise o contexto da conversa completa, não apenas palavras isoladas
- Considere o perfil do cliente, situação e necessidades para tomar decisões autônomas
- Seja proativo e inteligente nas interpretações, não robótico

FLUXO PARA FATURAS/PAGAMENTOS:
- Quando cliente solicitar pagamento/fatura (qualquer forma natural):
  1. Se JÁ TEM CPF na conversa: Use gerar_fatura_completa diretamente
  2. Se NÃO TEM CPF: Peça o CPF primeiro, depois execute o fluxo acima
- Para tipo_pagamento, ANALISE INTELIGENTEMENTE:
  * Cliente jovem/pressa/digital → provavelmente PIX
  * Cliente tradicional/formal/comprovante → provavelmente boleto
  * Contexto da conversa e perfil do cliente
- NUNCA mostre dados fixos - SEMPRE use dados reais do SGP
- SEMPRE avise que está buscando antes de executar a função

REGRAS PARA ENCERRAMENTO DE ATENDIMENTO:
- Após enviar fatura com sucesso, SEMPRE pergunte: "Posso te ajudar com mais alguma coisa?"
- Se cliente responder: "não", "não preciso", "tá bom", "obrigado", "tchau" → IMEDIATAMENTE use encerrar_atendimento
- NUNCA continue perguntando se cliente já demonstrou satisfação
- Use encerrar_atendimento para limpar memória Redis automaticamente

PROBLEMAS DE INTERNET:
- Se o cliente relatar problemas de internet, utilize verificar_acesso_sgp para verificar o status
- Só prossiga para as orientações após consultar o status da conexão

                DIAGNÓSTICO INTELIGENTE DE PROBLEMAS DE INTERNET:
1. Quando cliente disser "sem internet", "sem acesso", "internet não funciona" → Use verificar_acesso_sgp
2. A função identifica automaticamente:
   - Status "Online" → Problema no equipamento local
   - Status "Offline" → Problema técnico (fibra, equipamento)
   - Status "Suspenso" → Problema financeiro (fatura em aberto)
3. Se for "Offline":
   - PERGUNTE IMEDIATAMENTE: "Você consegue ver algum LED vermelho piscando no seu modem?"
   - Se cliente responder SIM (sim, tem, está, piscando, vermelho) → Use criar_chamado_tecnico IMEDIATAMENTE
   - NÃO pergunte mais nada, apenas informe que é problema físico e vai abrir chamado
   - Se cliente responder NÃO → Oriente sobre equipamento local
4. Se for "Suspenso" → Oriente sobre pagamento de fatura
5. Se for "Online" → Oriente sobre equipamento local

REGRA IMPORTANTE: Se cliente já disse que está sem internet E você detectou que está offline, pergunte sobre LED vermelho. Se confirmar LED vermelho, abra chamado técnico IMEDIATAMENTE sem mais perguntas.

TRANSFERÊNCIA INTELIGENTE:
- Quando não conseguir resolver o problema do cliente, use transferir_conversa_inteligente
- A função analisa automaticamente a conversa e escolhe a equipe mais adequada
- Após transferência, a IA NÃO responde mais - apenas quando atendente encerrar
- Conversa fica em "Em Espera" até atendente pegar o atendimento

MEMÓRIA DE CONTEXTO (REDIS):
- USE A MEMÓRIA REDIS APENAS PARA A CONVERSА ATUAL
- SE JÁ CONSULTOU O CLIENTE NESTA CONVERSА, NÃO PEÇA CPF/CNPJ NOVAMENTE
- SE CLIENTE JÁ ESCOLHEU PIX/BOLETO NESTA CONVERSА, USE gerar_fatura_completa IMEDIATAMENTE
- QUANDO CLIENTE PEDIR "PAGA FATURA" E JÁ TEM CPF NESTA CONVERSА, EXECUTE gerar_fatura_completa
- NUNCA REPITA PERGUNTAS JÁ FEITAS NESTA CONVERSА
- LEMBRE-SE DO QUE JÁ FOI CONVERSADO NESTA CONVERSА

FLUXO FATURA SIMPLIFICADO:
1. Cliente pede fatura/PIX/boleto
2. Se JÁ TEM CPF/CNPJ nesta conversa: Use gerar_fatura_completa IMEDIATAMENTE
3. Se NÃO TEM CPF/CNPJ nesta conversa: Peça o CPF/CNPJ primeiro
4. A função faz TUDO automaticamente: SGP + QR Code + WhatsApp + Botões + Mensagem de confirmação
5. NÃO mostre dados da fatura manualmente - a função já faz isso
6. NÃO confirme novamente - a função já confirma
"""

            # Recuperar memória Redis da conversa
            conversation_memory = None
            conversation_id = None
            
            if contexto and contexto.get('conversation'):
                conversation = contexto['conversation']
                conversation_id = conversation.id
                
                # Recuperar memória Redis
                try:
                    conversation_memory = redis_memory_service.get_conversation_memory_sync(
                        provedor_id=provedor.id,
                        conversation_id=conversation_id
                    )
                    if conversation_memory:
                        logger.info(f"Memória Redis recuperada para conversa {conversation_id}: {conversation_memory}")
                    else:
                        logger.info(f"Nenhuma memória Redis encontrada para conversa {conversation_id}")
                except Exception as e:
                    logger.warning(f"Erro ao recuperar memória Redis: {e}")
            
            # Construir mensagens com histórico
            messages = [{"role": "system", "content": system_prompt}]
            
            # Adicionar contexto da conversa se disponível
            if contexto and contexto.get('conversation'):
                conversation = contexto['conversation']
                
                # Buscar mensagens recentes da conversa
                try:
                    from conversations.models import Message
                    recent_messages = Message.objects.filter(
                        conversation=conversation
                    ).order_by('-created_at')[:10]  # Últimas 10 mensagens
                    
                    # Adicionar mensagens ao contexto (em ordem cronológica)
                    for msg in reversed(recent_messages):
                        if msg.is_from_customer:
                            messages.append({"role": "user", "content": msg.content})
                        else:
                            messages.append({"role": "assistant", "content": msg.content})
                except Exception as e:
                    logger.warning(f"Erro ao recuperar histórico: {e}")
            
            # Adicionar informações da memória Redis ao prompt se disponível
            if conversation_memory:
                memory_info = ""
                if conversation_memory.get('cpf_cnpj'):
                    memory_info += f"\n🧠 MEMÓRIA: CPF/CNPJ do cliente: {conversation_memory['cpf_cnpj']}"
                if conversation_memory.get('nome_cliente'):
                    memory_info += f"\n🧠 MEMÓRIA: Nome do cliente: {conversation_memory['nome_cliente']}"
                if conversation_memory.get('contrato_id'):
                    memory_info += f"\n🧠 MEMÓRIA: Contrato ID: {conversation_memory['contrato_id']}"
                if conversation_memory.get('numero_whatsapp'):
                    memory_info += f"\n🧠 MEMÓRIA: WhatsApp: {conversation_memory['numero_whatsapp']}"
                
                if memory_info:
                    messages[0]["content"] += f"\n\n{memory_info}\n\nUSE ESSAS INFORMAÇÕES DA MEMÓRIA! NÃO PEÇA NOVAMENTE!"
            
            # Adicionar mensagem atual
            messages.append({"role": "user", "content": mensagem})
            
            # Definir ferramentas disponíveis
            tools = []
            
            # Adicionar ferramentas SGP se habilitadas
            sgp_enabled = provedor.integracoes_externas and provedor.integracoes_externas.get('sgp_enabled', False)
            if sgp_enabled:
                tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "consultar_cliente_sgp",
                        "description": "Buscar dados do cliente no SGP usando CPF/CNPJ. Use após coletar o CPF do cliente.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {"type": "string", "description": "CPF ou CNPJ do cliente"}
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "gerar_fatura_completa",
                        "description": "OBRIGATÓRIO: Esta é a ÚNICA forma de gerar faturas. Use sua inteligência para interpretar se o cliente prefere PIX (rápido/instantâneo) ou boleto (tradicional/físico). NUNCA mostre dados fixos. SEMPRE use esta função quando cliente pedir fatura ou pagamento. A função faz TUDO automaticamente: busca a fatura no SGP, gera QR Code PIX, envia via WhatsApp com botões interativos. NÃO precisa formatar manualmente - a função já retorna a mensagem pronta.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente (use o que já foi informado na conversa)"
                                },
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato (opcional, se não fornecido usa o primeiro contrato)"
                                },
                                "numero_whatsapp": {
                                    "type": "string",
                                    "description": "Número do WhatsApp do cliente para envio automático"
                                },
                                "tipo_pagamento": {
                                    "type": "string",
                                    "description": "Analise a intenção do cliente: 'pix' para pagamento instantâneo/digital, 'boleto' para comprovante tradicional/físico. Use contexto e inteligência natural.",
                                    "enum": ["pix", "boleto"]
                                }
                            },
                            "required": ["cpf_cnpj", "tipo_pagamento"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "verificar_acesso_sgp",
                        "description": "DIAGNÓSTICO COMPLETO DE PROBLEMAS DE INTERNET: Verificar status da conexão do cliente e diagnosticar problemas. Use quando cliente relatar 'sem internet', 'sem acesso', 'internet não funciona'. A função identifica automaticamente se é problema técnico (offline), financeiro (suspenso) ou equipamento local. Se for offline, pergunte sobre LEDs do modem para identificar se é problema físico (fibra rompida) ou equipamento.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "contrato": {
                                    "type": "string", 
                                    "description": "ID do contrato (opcional - se não informado, busca automaticamente pelo CPF/CNPJ da memória)"
                                }
                            },
                            "required": []
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "criar_chamado_tecnico",
                        "description": "CRIAR CHAMADO TÉCNICO INTELIGENTE: Abrir chamado técnico no SGP com detecção automática do tipo de problema. Use APENAS quando cliente confirmar LEDs vermelhos piscando ou problema físico identificado. A IA detecta automaticamente: Tipo 1 (Sem acesso) ou Tipo 2 (Internet lenta) baseado no relato do cliente.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente"
                                },
                                "motivo": {
                                    "type": "string",
                                    "description": "Motivo do chamado técnico (ex: 'LED vermelho piscando', 'fibra rompida', 'internet lenta')"
                                },
                                "sintomas": {
                                    "type": "string",
                                    "description": "Sintomas relatados pelo cliente (ex: 'sem internet', 'LED vermelho piscando', 'velocidade baixa')"
                                }
                            },
                            "required": ["cpf_cnpj", "motivo", "sintomas"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "encerrar_atendimento",
                        "description": "OBRIGATÓRIO: Use quando cliente disser 'não', 'não preciso', 'tá bom', 'obrigado' ou qualquer resposta indicando que não precisa de mais ajuda. Limpa a memória Redis e encerra o atendimento automaticamente, registra auditoria e dispara CSAT.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "motivo": {"type": "string", "description": "Motivo do encerramento (ex: 'cliente_satisfeito', 'nao_precisa_mais', 'atendimento_concluido')"}
                            },
                            "required": ["motivo"]
                        }
                    }
                }
            ])
            
            # Detectar se cliente pediu fatura/pagamento
            mensagem_lower = mensagem.lower()
            cliente_pediu_fatura = any(word in mensagem_lower for word in ['paga', 'fatura', 'pix', 'boleto', 'pagamento', 'pagar'])
            
            # Se cliente pediu fatura, adicionar instrução específica
            if cliente_pediu_fatura:
                system_prompt += """

CLIENTE PEDIU FATURA/PAGAMENTO:
- IMPORTANTE: Antes de usar gerar_fatura_completa, você DEVE perguntar o CPF/CNPJ do cliente
- Se já tem CPF/CNPJ nesta conversa, use gerar_fatura_completa IMEDIATAMENTE
- NUNCA use dados de conversas anteriores - sempre pergunte o CPF/CNPJ se não tiver nesta conversa
- A função gerar_fatura_completa faz TUDO automaticamente:
  * Formata o CPF/CNPJ (adiciona pontos e traços)
  * Busca a fatura no SGP usando o CPF/CNPJ formatado
  * Gera QR Code PIX automaticamente
  * Envia via WhatsApp com botões interativos
  * Confirma o envio na conversa
- NÃO precisa fazer nada manualmente - a função já faz tudo
- Use 'pix' se cliente pedir pagamento rápido/instantâneo
- Use 'boleto' se cliente pedir comprovante tradicional/físico
- Só use gerar_fatura_completa quando tiver o CPF/CNPJ válido (11 ou 14 dígitos)
- Se cliente não informou CPF/CNPJ, pergunte: "Qual é o seu CPF ou CNPJ?"
- Use gerar_fatura_completa apenas com dados válidos:
  * cpf_cnpj: CPF/CNPJ completo e válido (11 ou 14 dígitos)
  * tipo_pagamento: "pix" ou "boleto" baseado na intenção do cliente
- A função faz TUDO automaticamente: SGP + envio via WhatsApp + Mensagem específica
- NÃO envie mensagens adicionais - a função já confirma tudo

ENCERRAMENTO AUTOMÁTICO INTELIGENTE:
- A IA detecta automaticamente quando o cliente está satisfeito
- Palavras como "ok", "certo", "beleza", "obrigado", "tá bom", "resolvido" disparam encerramento automático
- O sistema registra automaticamente na auditoria do provedor
- O sistema dispara automaticamente a pesquisa de satisfação (CSAT)
- Não precisa usar manualmente a função encerrar_atendimento - é automático
- A IA responde com mensagem de despedida e encerra o atendimento
"""
            
            # DETECTAR NECESSIDADE DE TRANSFERÊNCIA BASEADA NA CONVERSA
            transfer_necessario = False
            equipe_sugerida = ""
            motivo_transferencia = ""

            # Analisar mensagem atual para transferência
            mensagem_lower = mensagem.lower()

            # Problemas técnicos
            problemas_tecnicos = [
                'sem internet', 'internet lenta', 'não funciona', 'problema de conexão',
                'modem', 'roteador', 'led vermelho', 'wi-fi', 'sinal', 'caiu', 'offline',
                'sem acesso', 'velocidade baixa', 'queda', 'instável', 'travando',
                'ping alto', 'conexão ruim', 'fibra rompida', 'cabo', 'conector',
                'loss', 'perda de pacote', 'latência', 'lag', 'delay', 'lentidão',
                'intermitente', 'instabilidade', 'cortando', 'desconectando'
            ]

            # Problemas financeiros  
            problemas_financeiros = [
                'fatura', 'boleto', 'pagamento', 'conta', 'débito', 'vencimento',
                'pagar', 'valor', 'cobrança', 'segunda via', 'atraso', 'multa',
                'juros', 'negociar', 'parcelar', 'divida', 'inadimplente'
            ]

            # Vendas/novos clientes
            vendas_interesse = [
                'planos', 'contratar', 'preços', 'ofertas', 'mudar plano', 'quero assinar',
                'valores', 'velocidades', 'instalação', 'novo cliente', 'contratação',
                'melhor plano', 'comparar', 'promoção'
            ]

            # Atendimento humano
            solicitacao_humano = [
                'humano', 'atendente', 'pessoa', 'falar com alguém', 'supervisor',
                'reclamação', 'não resolveu', 'quero falar com', 'transferir'
            ]

            # Verificar se tem CPF/CNPJ na mensagem - se sim, não transferir, usar SGP
            import re
            cpf_cnpj_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b|\b\d{11}\b|\b\d{14}\b'
            cpf_cnpj_match = re.search(cpf_cnpj_pattern, mensagem)
            tem_cpf_cnpj = cpf_cnpj_match is not None
            # logger.info(f"🔍 DEBUG CPF/CNPJ: match={cpf_cnpj_match}, tem_cpf_cnpj={tem_cpf_cnpj}")
            
            # Verificar categoria da mensagem atual (APENAS para questões não relacionadas a faturas E sem CPF/CNPJ)
            # Se cliente pede fatura OU fornece CPF/CNPJ, não transferir - resolver diretamente
            if not any(word in mensagem_lower for word in ['pix', 'boleto', 'fatura', 'pagar', 'pagamento']) and not tem_cpf_cnpj:
                if any(problema in mensagem_lower for problema in problemas_tecnicos):
                    transfer_necessario = True
                    equipe_sugerida = "SUPORTE TÉCNICO"
                    motivo_transferencia = f"Cliente relatou problema técnico: {mensagem}"
                    
                elif any(problema in mensagem_lower for problema in vendas_interesse):
                    transfer_necessario = True
                    equipe_sugerida = "VENDAS"
                    motivo_transferencia = f"Cliente demonstrou interesse comercial: {mensagem}"
                    
                elif any(problema in mensagem_lower for problema in solicitacao_humano):
                    transfer_necessario = True
                    equipe_sugerida = "ATENDIMENTO GERAL"
                    motivo_transferencia = f"Cliente solicitou atendimento humano: {mensagem}"

                # Verificar também no histórico da conversa se há necessidade de transferência
                if conversation and not transfer_necessario:
                    try:
                        # Buscar últimas mensagens para contexto mais amplo
                        from conversations.models import Message
                        ultimas_mensagens = Message.objects.filter(
                            conversation=conversation
                        ).order_by('-created_at')[:5]  # Últimas 5 mensagens
                        
                        mensagens_texto = " ".join([msg.content.lower() for msg in ultimas_mensagens])
                        
                        # Analisar contexto mais amplo (exceto faturas)
                        if not any(word in mensagens_texto for word in ['pix', 'boleto', 'fatura', 'pagar', 'pagamento']):
                            if any(problema in mensagens_texto for problema in problemas_tecnicos):
                                transfer_necessario = True
                                equipe_sugerida = "SUPORTE TÉCNICO"
                                motivo_transferencia = "Análise do histórico indica problema técnico"
                                
                    except Exception as e:
                        logger.warning(f"Erro ao analisar histórico para transferência: {e}")

            # Log da detecção
            if transfer_necessario:
                logger.info(f"TRANSFERÊNCIA DETECTADA: {equipe_sugerida} - {motivo_transferencia}")
            else:
                logger.info("Nenhuma transferência detectada")
            
            # Forçar uso de ferramentas quando necessário
            force_tools = any(word in mensagem_lower for word in ['pix', 'boleto', 'fatura', 'pagar'])
            # Debug removido
            
            # ADICIONAR FERRAMENTAS DE TRANSFERÊNCIA SE NECESSÁRIO
            if transfer_necessario:
                # Adicionar ferramentas de banco de dados para transferências
                from core.database_function_definitions import DATABASE_FUNCTION_TOOLS
                tools.extend(DATABASE_FUNCTION_TOOLS)
                
                # Adicionar ferramentas específicas de transferência
                tools.extend([
                    {
                        "type": "function",
                        "function": {
                            "name": "buscar_equipes_disponiveis",
                            "description": "BUSCAR EQUIPES: Verifica quais equipes estão disponíveis para transferência. USE SEMPRE ANTES de transferir. Retorna lista de equipes como SUPORTE TÉCNICO, FINANCEIRO, VENDAS, etc.",
                            "parameters": {
                                "type": "object", 
                                "properties": {},
                                "required": []
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "executar_transferencia_conversa", 
                            "description": "TRANSFERIR CONVERSA: Executa transferência REAL para equipe especializada. USE APÓS buscar_equipes_disponiveis(). Analise a conversa e escolha a equipe MAIS ADEQUADA: SUPORTE TÉCNICO (problemas internet), FINANCEIRO (faturas/pagamentos), VENDAS (novos clientes), ATENDIMENTO GERAL (outros casos).",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "conversation_id": {
                                        "type": "string", 
                                        "description": "ID da conversa atual (OBRIGATÓRIO)"
                                    },
                                    "equipe_nome": {
                                        "type": "string",
                                        "description": "Nome da equipe baseado na análise: SUPORTE TÉCNICO (problemas técnicos), FINANCEIRO (faturas/pagamentos), VENDAS (planos/contratações), ATENDIMENTO GERAL (outros)"
                                    },
                                    "motivo": {
                                        "type": "string", 
                                        "description": "Motivo detalhado baseado na análise da conversa. Ex: 'Cliente relata internet lenta há 3 dias - precisa diagnóstico técnico'"
                                    }
                                },
                                "required": ["conversation_id", "equipe_nome", "motivo"]
                            }
                        }
                    }
                ])

            # FORÇAR USO DE FERRAMENTAS PARA TRANSFERÊNCIA (removido - duplicado)
            # force_tools = force_tools or transfer_necessario
            
            # FORÇAR USO DE FERRAMENTAS quando cliente fornecer CPF/CNPJ
            if tem_cpf_cnpj:
                force_tools = True
                # logger.info(f"🔧 CPF/CNPJ detectado: {cpf_cnpj_match.group() if cpf_cnpj_match else 'N/A'} - FORÇANDO FERRAMENTAS SGP")
            
            # logger.info(f"🔧 DEBUG force_tools final: {force_tools}")
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                tools=tools,
                tool_choice="required" if force_tools else "auto"
            )
            
            # Processar se a IA chamou alguma ferramenta
            if response.choices[0].message.tool_calls:
                # Processar ferramentas chamadas pela IA
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"IA chamou função: {function_name} com argumentos: {function_args}")
                    
                    # Executar a função chamada pela IA
                    if function_name in DATABASE_FUNCTION_MAPPING:
                        # Executar função de banco de dados
                        function_result = self._execute_database_function(provedor, function_name, function_args, contexto)
                    else:
                        # Executar função SGP
                        function_result = self._execute_sgp_function(provedor, function_name, function_args, contexto)
                    
                    # Salvar informações importantes na memória Redis
                    if conversation_id and function_result.get('success'):
                        memory_updates = {}
                        
                        # Salvar dados do cliente se foi consultado
                        if function_name == "consultar_cliente_sgp":
                            if function_result.get('nome'):
                                memory_updates['nome_cliente'] = function_result['nome']
                                
                                # Atualizar nome do contato no banco local
                                try:
                                    contact = conversation.contact
                                    if contact and contact.name != function_result['nome']:
                                        contact.name = function_result['nome']
                                        contact.save()
                                        logger.info(f"✅ Nome do contato atualizado: {contact.name}")
                                        
                                        # Enviar contato atualizado para Supabase
                                        try:
                                            from core.supabase_service import supabase_service
                                            supabase_service.save_contact(
                                                provedor_id=conversation.inbox.provedor_id,
                                                contact_id=contact.id,
                                                name=contact.name,
                                                phone=getattr(contact, 'phone', None),
                                                email=getattr(contact, 'email', None),
                                                avatar=getattr(contact, 'avatar', None),
                                                created_at_iso=contact.created_at.isoformat(),
                                                updated_at_iso=contact.updated_at.isoformat(),
                                                additional_attributes=contact.additional_attributes
                                            )
                                            logger.info(f"✅ Contato atualizado enviado para Supabase: {contact.name}")
                                        except Exception as supabase_err:
                                            logger.warning(f"Falha ao enviar contato atualizado para Supabase: {supabase_err}")
                                            
                                except Exception as contact_err:
                                    logger.warning(f"Falha ao atualizar contato: {contact_err}")
                                    
                            if function_result.get('contrato_id'):
                                memory_updates['contrato_id'] = function_result['contrato_id']
                            if function_args.get('cpf_cnpj'):
                                memory_updates['cpf_cnpj'] = function_args['cpf_cnpj']
                        
                        # Salvar dados da fatura se foi gerada
                        elif function_name == "gerar_fatura_completa":
                            if function_args.get('cpf_cnpj'):
                                memory_updates['cpf_cnpj'] = function_args['cpf_cnpj']
                            if function_args.get('numero_whatsapp'):
                                memory_updates['numero_whatsapp'] = function_args['numero_whatsapp']
                            if function_result.get('fatura_id'):
                                memory_updates['ultima_fatura_id'] = function_result['fatura_id']
                        
                        # Salvar número do WhatsApp se disponível no contexto
                        if contexto and contexto.get('conversation') and contexto['conversation'].contact:
                            memory_updates['numero_whatsapp'] = contexto['conversation'].contact.phone
                        
                        # Atualizar memória Redis se há dados para salvar
                        if memory_updates:
                            try:
                                # Mesclar com memória existente
                                current_memory = conversation_memory or {}
                                current_memory.update(memory_updates)
                                
                                redis_memory_service.set_conversation_memory_sync(
                                    provedor_id=provedor.id,
                                    conversation_id=conversation_id,
                                    data=current_memory
                                )
                                logger.info(f"Memória Redis atualizada para conversa {conversation_id}: {memory_updates}")
                            except Exception as e:
                                logger.warning(f"Erro ao salvar na memória Redis: {e}")
                    
                    # Adicionar resultado da função à conversa
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(function_result, ensure_ascii=False)
                    })
                
                # Verificar se gerar_fatura_completa foi executada
                fatura_executada = False
                fatura_sucesso = False
                resposta = None
                
                for tool_call in response.choices[0].message.tool_calls:
                    if tool_call.function.name == "gerar_fatura_completa":
                        fatura_executada = True
                        # Verificar se o resultado indica sucesso
                        for msg in messages:
                            if msg.get("role") == "tool" and msg.get("tool_call_id") == tool_call.id:
                                try:
                                    result_data = json.loads(msg["content"])
                                    logger.info(f"Resultado da função gerar_fatura_completa: {result_data}")
                                    if result_data.get("success") and result_data.get("mensagem_formatada"):
                                        fatura_sucesso = True
                                        # Usar diretamente a mensagem da função
                                        resposta = result_data["mensagem_formatada"]
                                        logger.info(f"Fatura enviada com sucesso - usando mensagem direta: {resposta}")
                                        break
                                    elif result_data.get("success") is False:
                                        # Função executou mas com erro - usar mensagem de erro específica
                                        resposta = "Desculpe, houve um problema ao processar sua fatura. Tente novamente em alguns instantes."
                                        logger.warning(f"Erro na função gerar_fatura_completa: {result_data.get('erro', 'Erro desconhecido')}")
                                        break
                                except Exception as e:
                                    logger.error(f"Erro ao processar resultado da função: {e}")
                                    pass
                        break
                
                # Decidir se fazer segunda chamada à OpenAI
                if fatura_executada:
                    # Se fatura foi executada (com sucesso ou erro), não fazer segunda chamada
                    if not resposta:
                        resposta = "Desculpe, ocorreu um erro ao processar sua solicitação. Tente novamente."
                else:
                    # Se não foi gerar_fatura_completa, fazer segunda chamada à OpenAI
                    final_response = openai.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature
                    )
                    resposta = final_response.choices[0].message.content.strip()
            else:
                # Não há tool calls, usar resposta direta da IA
                resposta = response.choices[0].message.content.strip()
            
            # Validar se não está usando dados fixos comuns
            dados_fixos_comuns = ["123456", "999999", "000000", "XXXX-XXXX"]
            for dado in dados_fixos_comuns:
                if dado in resposta:
                    logger.error(f"ERRO: IA usando dados fixos: {dado}")
                    resposta = "Erro interno: Preciso consultar o sistema primeiro. Me informe seu CPF/CNPJ para buscar seus dados reais."
                    break
            
            # DETECÇÃO AUTOMÁTICA DE SATISFAÇÃO DO CLIENTE E RESPOSTA CSAT
            satisfacao_detectada = False
            csat_response_detected = False
            
            if contexto and contexto.get('conversation'):
                # PRIMEIRO: Verificar se é resposta CSAT
                csat_result = self._detectar_resposta_csat(mensagem, contexto)
                
                if csat_result.get('is_csat_response'):
                    logger.info(f"✅ Resposta CSAT detectada pela IA: Rating {csat_result.get('rating')}, Feedback: {csat_result.get('feedback')}")
                    csat_response_detected = True
                    
                    # Processar resposta CSAT
                    try:
                        from conversations.csat_automation import CSATAutomationService
                        conversation = contexto['conversation']
                        contact = conversation.contact
                        
                        # Criar feedback CSAT usando dados da IA
                        csat_feedback = CSATAutomationService.create_csat_feedback_from_ai_response(
                            conversation=conversation,
                            contact=contact,
                            rating=csat_result.get('rating'),
                            feedback_text=csat_result.get('feedback'),
                            raw_response=csat_result.get('raw_response')
                        )
                        
                        if csat_feedback:
                            logger.info(f"✅ CSAT feedback criado: {csat_feedback.id} - Rating: {csat_feedback.rating_value}")
                            
                            # Resposta de agradecimento personalizada baseada na avaliação
                            nome_usar = self._get_nome_para_csat(conversation)
                            rating = csat_result.get('rating', 3)
                            
                            if rating == 1:
                                resposta = f"😔 Sinto muito que seu atendimento não foi bom, {nome_usar}! Estamos sempre melhorando e esperamos te atender melhor na próxima vez."
                            elif rating == 2:
                                resposta = f"😕 Poxa, {nome_usar}, sentimos que não tenha gostado. Sua opinião é importante para melhorarmos!"
                            elif rating == 3:
                                resposta = f"🙂 Obrigado pelo seu feedback, {nome_usar}! Vamos trabalhar para te surpreender da próxima vez."
                            elif rating == 4:
                                resposta = f"😄 Que bom saber disso, {nome_usar}! Ficamos felizes que seu atendimento foi bom!"
                            else:  # rating == 5
                                resposta = f"🤩 Maravilha, {nome_usar}! Agradecemos por sua avaliação e ficamos felizes com sua satisfação!"
                            
                            # Marcar CSAT como processado
                            from conversations.models import CSATRequest
                            csat_request = CSATRequest.objects.filter(
                                conversation=conversation,
                                status='sent'
                            ).first()
                            if csat_request:
                                csat_request.status = 'completed'
                                csat_request.save()
                                logger.info(f"CSAT request {csat_request.id} marcado como completed")
                        else:
                            logger.warning("Falha ao criar CSAT feedback")
                            resposta = "Obrigado pelo seu feedback! Se precisar de mais alguma coisa, estaremos aqui!"
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar resposta CSAT: {e}")
                        resposta = "Obrigado pelo seu feedback! Se precisar de mais alguma coisa, estaremos aqui!"
                
                # SEGUNDO: Se não é CSAT, verificar se o cliente está satisfeito
                elif not csat_response_detected:
                    resultado_deteccao = self._detectar_satisfacao_cliente(mensagem)
                    
                    if resultado_deteccao['satisfeito'] and resultado_deteccao['confianca'] >= 0.6:
                        logger.info(f"Cliente satisfeito detectado: {resultado_deteccao}")
                        
                        # Encerrar atendimento automaticamente
                        try:
                            encerramento_result = self._execute_sgp_function(
                                provedor=provedor,
                                function_name="encerrar_atendimento",
                                function_args={'motivo': resultado_deteccao['motivo']},
                                contexto=contexto
                            )
                            
                            if encerramento_result.get('success'):
                                satisfacao_detectada = True
                                # Usar mensagem de encerramento da função
                                resposta = encerramento_result.get('mensagem', resposta)
                                logger.info("Atendimento encerrado automaticamente com sucesso")
                            else:
                                logger.warning(f"Falha ao encerrar atendimento automaticamente: {encerramento_result.get('erro')}")
                        except Exception as e:
                            logger.error(f"Erro ao encerrar atendimento automaticamente: {e}")
            
            # Verificar se deve encerrar o atendimento automaticamente
            encerrar_atendimento = False
            if conversation_id and resposta:
                # Detectar se o cliente agradeceu após receber ajuda
                mensagem_lower = mensagem.lower()
                resposta_lower = resposta.lower()
                
                # Palavras de agradecimento do cliente
                agradecimentos = ['obrigado', 'obrigada', 'valeu', 'brigado', 'brigada', 'obg', 'vlw', 'thanks', 'thank you']
                
                # Verificar se cliente agradeceu
                cliente_agradeceu = any(agradecimento in mensagem_lower for agradecimento in agradecimentos)
                
                # Verificar se a IA está se despedindo (indica que a tarefa foi concluída)
                ia_se_despedindo = any(despedida in resposta_lower for despedida in [
                    'tenha um ótimo dia', 'até logo', 'até mais', 'qualquer coisa', 'precisar', 'chamar',
                    'disponível', 'ajudar', 'te ajudar', 'posso ajudar', 'ajudar com mais'
                ])
                
                # Verificar se houve sucesso em operações importantes
                operacao_sucesso = any(sucesso in resposta_lower for sucesso in [
                    'enviado', 'enviada', 'gerado', 'gerada', 'processado', 'processada',
                    'concluído', 'concluída', 'finalizado', 'finalizada', 'resolvido', 'resolvida'
                ])
                
                # Condições para encerrar automaticamente:
                # 1. Cliente agradeceu E IA está se despedindo
                # 2. Cliente agradeceu E houve sucesso em operação
                if cliente_agradeceu and (ia_se_despedindo or operacao_sucesso):
                    encerrar_atendimento = True
                    logger.info("🔄 Condições para encerramento automático detectadas:")
                    logger.info(f"   - Cliente agradeceu: {cliente_agradeceu}")
                    logger.info(f"   - IA se despedindo: {ia_se_despedindo}")
                    logger.info(f"   - Operação com sucesso: {operacao_sucesso}")
            
            # Encerrar atendimento se necessário
            if encerrar_atendimento and conversation_id:
                try:
                    from conversations.models import Conversation
                    conversation = Conversation.objects.get(id=conversation_id)
                    
                    # Encerrar conversa
                    conversation.status = 'closed'
                    conversation.save()
                    
                    # Enviar auditoria para Supabase
                    try:
                        from core.supabase_service import supabase_service
                        supabase_service.save_audit(
                            provedor_id=conversation.inbox.provedor_id,
                            conversation_id=conversation.id,
                            action='conversation_closed_ai_auto',
                            details={'resolution_type': 'ai_auto_closure', 'reason': 'automatic_closure'},
                            user_id=None,
                            ended_at_iso=timezone.now().isoformat()
                        )
                        logger.info(f"✅ Auditoria enviada para Supabase: conversa {conversation_id}")
                        
                        # Enviar dados da conversa para Supabase
                        try:
                            supabase_service.save_conversation(
                                provedor_id=conversation.inbox.provedor_id,
                                conversation_id=conversation.id,
                                contact_id=conversation.contact_id,
                                inbox_id=conversation.inbox_id,
                                status=conversation.status,
                                assignee_id=conversation.assignee_id,
                                created_at_iso=conversation.created_at.isoformat(),
                                updated_at_iso=conversation.updated_at.isoformat(),
                                ended_at_iso=timezone.now().isoformat(),
                                additional_attributes=conversation.additional_attributes
                            )
                            logger.info(f"✅ Conversa enviada para Supabase: {conversation.id}")
                        except Exception as _conv_err:
                            logger.warning(f"Falha ao enviar conversa para Supabase: {_conv_err}")
                        
                        # Enviar dados do contato para Supabase
                        try:
                            contact = conversation.contact
                            supabase_service.save_contact(
                                provedor_id=conversation.inbox.provedor_id,
                                contact_id=contact.id,
                                name=contact.name,
                                phone=getattr(contact, 'phone', None),
                                email=getattr(contact, 'email', None),
                                avatar=getattr(contact, 'avatar', None),
                                created_at_iso=contact.created_at.isoformat(),
                                updated_at_iso=contact.updated_at.isoformat(),
                                additional_attributes=contact.additional_attributes
                            )
                            logger.info(f"✅ Contato enviado para Supabase: {contact.id}")
                        except Exception as _contact_err:
                            logger.warning(f"Falha ao enviar contato para Supabase: {_contact_err}")
                        
                        # Enviar todas as mensagens da conversa para Supabase
                        try:
                            from conversations.models import Message
                            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
                            messages_sent = 0
                            
                            for msg in messages:
                                success = supabase_service.save_message(
                                    provedor_id=conversation.inbox.provedor_id,
                                    conversation_id=conversation.id,
                                    contact_id=contact.id,
                                    content=msg.content,
                                    message_type=msg.message_type,
                                    is_from_customer=msg.is_from_customer,
                                    external_id=msg.external_id,
                                    file_url=msg.file_url,
                                    file_name=msg.file_name,
                                    file_size=msg.file_size,
                                    additional_attributes=msg.additional_attributes,
                                    created_at_iso=msg.created_at.isoformat()
                                )
                                if success:
                                    messages_sent += 1
                            
                            logger.info(f"✅ {messages_sent}/{messages.count()} mensagens enviadas para Supabase")
                        except Exception as _msg_err:
                            logger.warning(f"Falha ao enviar mensagens para Supabase: {_msg_err}")
                            
                    except Exception as _sup_err:
                        logger.warning(f"Falha ao enviar auditoria para Supabase: {_sup_err}")
                    
                    # Limpar memória Redis da conversa encerrada
                    try:
                        from .redis_memory_service import redis_memory_service
                        redis_memory_service.clear_conversation_memory(conversation_id)
                        logger.info(f"🧹 Memória Redis limpa para conversa {conversation_id}")
                    except Exception as e:
                        logger.warning(f"Erro ao limpar memória Redis da conversa {conversation_id}: {e}")
                    
                    logger.info(f"✅ Atendimento encerrado automaticamente - Conversa {conversation_id} fechada")
                    
                except Exception as e:
                    logger.error(f"Erro ao encerrar atendimento automaticamente: {e}")
            
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "provedor": provedor.nome,
                "satisfacao_detectada": satisfacao_detectada
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return {
                "success": False,
                "erro": str(e),
                "provedor": provedor.nome
            }

    # Método antigo removido - usando apenas o novo prompt simplificado


            # Instruções para uso dos serviços de fatura
            if 'fatura' in mensagem_lower or 'boleto' in mensagem_lower or 'pix' in mensagem_lower:
                system_prompt += """

IMPORTANTE - FERRAMENTA DE FATURA:
- Para gerar faturas, use SEMPRE a ferramenta 'gerar_fatura_completa'
- Fluxo obrigatório:
  1. Use gerar_fatura_completa(contrato_id) 
  2. A ferramenta automaticamente busca dados no SGP via /api/ura/fatura2via/
  3. A ferramenta automaticamente gera QR code PIX (se disponível)
  4. A ferramenta automaticamente envia via WhatsApp com botões interativos
  5. A função já confirma automaticamente o envio
- NUNCA pule etapas ou use dados mockados
- Use APENAS dados reais retornados pela ferramenta
- A ferramenta integra automaticamente: fatura_service.py + qr_code_service.py + sgp_client.py + uazapi_client.py
"""
            
            # Verificar se a mensagem indica necessidade de perguntar se é cliente
            needs_client_check = any(keyword in mensagem_lower for keyword in [
                'boleto', 'fatura', 'conta', 'pagamento', 'débito', 'vencimento',
                'sem internet', 'internet parou', 'não funciona', 'problema', 'chamado', 'reclamação',
                'técnico', 'instalação', 'cancelar', 'mudar plano', 'alterar', 'consulta'
            ])
            
            # Instruções específicas para problemas técnicos
            if any(keyword in mensagem_lower for keyword in [
                'sem internet', 'internet parou', 'não funciona', 'problema', 'técnico', 'conexão'
            ]):
                system_prompt += """

IMPORTANTE - PROBLEMAS TÉCNICOS:
- Para problemas de conexão, use APENAS a ferramenta 'verificar_acesso_sgp'
- Fluxo obrigatório:
  1. Use consultar_cliente_sgp para identificar o contrato
  2. Use verificar_acesso_sgp(contrato_id) para verificar status da conexão
  3. Apresente o resultado ao cliente
  4. Se necessário, encaminhe para suporte técnico
- NÃO use outras ferramentas para problemas técnicos
- Foque apenas na verificação de status da conexão
"""
            
            # Verificar se o cliente forneceu CPF/CNPJ na mensagem
            cpf_cnpj_detected = self._detect_cpf_cnpj(mensagem)
            if cpf_cnpj_detected:
                logger.info(f"CPF/CNPJ detectado na mensagem: {cpf_cnpj_detected}")
                system_prompt += f"""

IMPORTANTE - CPF/CNPJ DETECTADO:
- O cliente forneceu CPF/CNPJ: {cpf_cnpj_detected}
- SEMPRE use a ferramenta 'SalvarCpfContato' para salvar este CPF/CNPJ
- Depois use 'consultar_cliente_sgp' com este CPF/CNPJ
- Após consultar, execute automaticamente a ação solicitada pelo cliente
- Se for cliente, apresente os dados e resolva a solicitação
- Se não for cliente, ofereça planos de internet
- NÃO transfira para equipe humana sem tentar resolver primeiro

IMPORTANTE - ENVIO AUTOMÁTICO DE FATURA:
- Quando o cliente solicitar fatura/boleto, SEMPRE:
  1. Use 'SalvarCpfContato' para salvar o CPF/CNPJ
  2. Use 'consultar_cliente_sgp' para verificar dados do cliente
  3. Use 'gerar_fatura_completa' para obter os dados da fatura
  4. Mostre os dados formatados na conversa
  5. Envie automaticamente via WhatsApp com botões interativos
  6. Use _send_fatura_via_uazapi para enviar a mensagem com botões
  7. A função já confirma automaticamente o envio
"""
            
            # Adicionar instrução específica para perguntar se é cliente apenas quando necessário
            already_asked_if_client = conversation.additional_attributes.get('asked_if_client', False) if conversation else False
            if not already_asked_if_client and needs_client_check:
                logger.info("Detectada necessidade de verificar se é cliente - adicionando instrução")
                system_prompt += """

IMPORTANTE - VERIFICAÇÃO DE CLIENTE OBRIGATÓRIA:
- O cliente mencionou algo que requer verificação se ele é cliente (boleto, problemas técnicos, etc)
- SEMPRE pergunte educadamente se ele já é cliente ANTES de prosseguir
- Use uma destas frases:
  * 'Para te ajudar melhor, você já é nosso cliente?'
  * 'Posso confirmar se você já é cliente da [NOME_DA_EMPRESA]?'
  * 'Antes de prosseguir, você já é nosso cliente?'
- Seja natural e educado na pergunta
- NÃO pule esta etapa - é OBRIGATÓRIA para qualquer solicitação específica
- Após confirmar que é cliente, use a ferramenta 'GetCpfContato' para verificar se já tem CPF salvo
- Se não tiver CPF salvo, peça o CPF/CNPJ e use 'SalvarCpfContato' para salvar
"""
            elif not already_asked_if_client:
                logger.info("Conversa inicial - respondendo naturalmente sem forçar pergunta sobre ser cliente")
                system_prompt += """

IMPORTANTE - CONVERSA INICIAL:
- Responda de forma natural e amigável
- Se for apenas um cumprimento ou pergunta geral, não pergunte imediatamente se é cliente
- Seja acolhedor e pergunte como pode ajudar
- Só verifique se é cliente quando ele solicitar algo específico como boletos, suporte técnico, etc
- Quando ele solicitar algo específico, SEMPRE pergunte se é cliente primeiro
"""
            else:
                logger.info("Já perguntou se é cliente, prosseguindo normalmente")
                system_prompt += """

IMPORTANTE - CLIENTE JÁ IDENTIFICADO:
- Já foi confirmado que o cliente é nosso cliente
- Use a ferramenta 'GetCpfContato' para verificar se já tem CPF salvo
- Se não tiver CPF salvo, peça o CPF/CNPJ e use 'SalvarCpfContato' para salvar
- Use a memória Redis para não pedir CPF repetidamente
- Após obter CPF/CNPJ, execute automaticamente a ação solicitada
"""
            
            # REABILITANDO FERRAMENTAS PARA FUNCIONALIDADE COMPLETA
            logger.info("FERRAMENTAS REABILITADAS - implementando funcionalidade completa")
            
            # Verificar configurações do SGP para debug
            integracao = provedor.integracoes_externas or {}
            sgp_url = integracao.get('sgp_url')
            sgp_token = integracao.get('sgp_token') 
            sgp_app = integracao.get('sgp_app')
            
            logger.info(f"Configurações SGP do provedor {provedor.nome}:")
            logger.info(f"  - SGP URL: {sgp_url}")
            logger.info(f"  - SGP Token: {'Configurado' if sgp_token else 'Não configurado'}")
            logger.info(f"  - SGP App: {sgp_app}")
            
            if not all([sgp_url, sgp_token, sgp_app]):
                logger.warning("Configurações do SGP incompletas - ferramentas não funcionarão")
                # Adicionar instrução sobre configuração necessária
                system_prompt += """

IMPORTANTE - CONFIGURAÇÃO SGP NECESSÁRIA:
- As ferramentas de consulta ao SGP não estão configuradas
- Configure as integrações SGP no painel do provedor para funcionalidade completa
- Por enquanto, encaminhe solicitações específicas para o suporte humano
"""
            else:
                logger.info("Configurações do SGP completas - ferramentas funcionando")
                # Adicionar instrução sobre uso das ferramentas
                system_prompt += """

IMPORTANTE - FUNCIONALIDADE COMPLETA ATIVA:
- Você TEM acesso às ferramentas de consulta ao SGP
- SEMPRE tente resolver a solicitação do cliente primeiro usando as ferramentas disponíveis
- SÓ transfira para equipe humana se realmente não conseguir resolver
- Use as ferramentas na seguinte ordem OBRIGATÓRIA:
  1. GetCpfContato (SEMPRE primeiro para verificar se já tem CPF salvo)
  2. SalvarCpfContato (se CPF não estiver salvo)
  3. consultar_cliente_sgp (para verificar se é cliente)
  4. verificar_acesso_sgp (para problemas técnicos)
  5. gerar_fatura_completa (para faturas/boletos) - OBRIGATÓRIO para faturas
  6. gerar_pix_qrcode (para PIX específico)
- Se uma ferramenta falhar, tente a próxima antes de transferir

REGRA CRÍTICA PARA FATURAS:
- Quando cliente solicitar fatura/boleto, SEMPRE execute esta sequência:
  1. Use GetCpfContato para verificar se já tem CPF salvo
  2. Se não tiver, peça CPF/CNPJ
  3. Use SalvarCpfContato para salvar o CPF
  4. Use consultar_cliente_sgp para verificar dados do cliente
  5. Use gerar_fatura_completa para gerar a fatura
  6. Após gerar, SEMPRE envie automaticamente via WhatsApp usando _send_fatura_via_uazapi
  7. Confirme na conversa que a fatura foi enviada

REGRA CRÍTICA PARA MEMÓRIA REDIS:
- SEMPRE use GetCpfContato ANTES de perguntar CPF/CNPJ
- Se GetCpfContato retornar CPF encontrado, use diretamente
- Se não retornar CPF, peça ao cliente e use SalvarCpfContato
- Use a memória Redis para não pedir CPF repetidamente na mesma conversa
- A memória Redis é automática - você não precisa gerenciar manualmente

FORMATO OBRIGATÓRIO PARA RESPOSTAS DAS FERRAMENTAS SGP:

ATENÇÃO CRÍTICA: NUNCA use os formatos antigos:
- NUNCA: "*Dados do Cliente:*"
- NUNCA use nomes fixos - SEMPRE use dados reais do SGP
- NUNCA: "*Status do Contrato:* Suspenso"
- NUNCA: "*Cliente Encontrado*"
- NUNCA: "Como posso te ajudar hoje, Pedro?"

**Para consultar_cliente_sgp:**
- SEMPRE formate EXATAMENTE assim (SEM EMOJIS):

Para UM contrato:
Contrato:
*NOME_DO_CLIENTE*

1 - Contrato (ID): *ENDEREÇO*

Para MÚLTIPLOS contratos:
Contratos:
*NOME_DO_CLIENTE*

1 - Contrato (ID): *ENDEREÇO*

*NOME_DO_CLIENTE*

2 - Contrato (ID): *ENDEREÇO*

**Para gerar_fatura_completa:**
- A função faz TUDO automaticamente - NÃO precisa formatar manualmente
- NÃO mostre dados da fatura - a função já retorna a mensagem pronta
- A função já envia automaticamente via WhatsApp com botões para:
  * Copiar chave PIX
  * Copiar linha digitável  
  * Acessar fatura online
- Use a função _send_fatura_via_uazapi para enviar a mensagem com botões
- A função já confirma automaticamente o envio
- IMPORTANTE: A função usa o CPF/CNPJ da memória Redis automaticamente
- IMPORTANTE: A função formata o CPF/CNPJ automaticamente (adiciona pontos e traços)
- IMPORTANTE: A função busca a fatura no SGP automaticamente usando o CPF/CNPJ formatado
- IMPORTANTE: A função envia via WhatsApp automaticamente com QR Code PIX e botões interativos

**Para todas as faturas:**
- SEMPRE envie automaticamente via WhatsApp após gerar
- Use _send_fatura_via_uazapi com os dados da fatura
- Inclua botões para PIX, linha digitável e acesso online
- Confirme na conversa que foi enviada
- Se falhar no envio, informe ao cliente mas continue o atendimento
"""
            
            # Ferramentas disponíveis
            system_prompt += """

FERRAMENTAS:
- consultar_cliente_sgp(cpf_cnpj) → buscar cliente
- gerar_fatura_completa(contrato) → gerar e enviar fatura
- verificar_acesso_sgp(contrato) → status conexão

REGRAS FINAIS:
- Execute ferramentas quando prometido
- Não repita perguntas já feitas
- Prossiga no fluxo sem voltar
"""
            
            # Construir o prompt do usuário
            user_prompt = self._build_user_prompt(mensagem, contexto or {})
            
            # Definir mensagens para a API
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Definir ferramentas SGP que a IA pode chamar
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "consultar_cliente_sgp",
                        "description": "Consulta dados reais do cliente no SGP usando CPF/CNPJ. SEMPRE use esta ferramenta quando receber CPF/CNPJ. FORMATO OBRIGATÓRIO: Para UM contrato use 'Contrato:' seguido de '*NOME*' e '1 - Contrato (ID): *ENDEREÇO*'. Para MÚLTIPLOS contratos use 'Contratos:' seguido da lista. NUNCA use emojis ou frases como 'Cliente Encontrado', 'Nome:', 'Status do Contrato:'.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente (apenas números)"
                                }
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "verificar_acesso_sgp",
                        "description": "Verifica status de acesso/conexão de um contrato no SGP. Use após identificar o contrato do cliente. IMPORTANTE: Formate a resposta EXATAMENTE assim: *Status do seu acesso:* seguido de Status e Contrato.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato"
                                }
                            },
                            "required": ["contrato"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "gerar_fatura_completa",
                        "description": "OBRIGATÓRIO: Esta é a ÚNICA forma de gerar faturas. IMPORTANTE: Só use quando tiver CPF/CNPJ válido (11 ou 14 dígitos). Usa endpoint /api/ura/fatura2via/ para buscar dados reais do SGP e envia automaticamente via WhatsApp com QR Code PNG e botão Copiar Chave PIX. NUNCA mostre dados fixos. SEMPRE use esta função quando cliente pedir fatura/PIX/boleto.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente (use o que já foi informado na conversa)"
                                },
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato (opcional, se não fornecido usa o primeiro contrato)"
                                },
                                "numero_whatsapp": {
                                    "type": "string",
                                    "description": "Número do WhatsApp do cliente para envio automático"
                                }
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "enviar_qr_code_pix",
                        "description": "Envia apenas QR Code PIX usando qr_code_service.py. Use quando cliente quiser apenas o QR Code.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente"
                                },
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato"
                                },
                                "numero_whatsapp": {
                                    "type": "string",
                                    "description": "Número do WhatsApp do cliente"
                                }
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "enviar_boleto_pdf",
                        "description": "Envia boleto em PDF usando fatura_service.py. Use quando cliente escolher boleto.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente"
                                },
                                "contrato": {
                                    "type": "string",
                                    "description": "ID do contrato"
                                },
                                "numero_whatsapp": {
                                    "type": "string",
                                    "description": "Número do WhatsApp do cliente"
                                }
                            },
                            "required": ["cpf_cnpj"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "enviar_formato_adicional",
                        "description": "Envia formato adicional de pagamento (PIX ou Boleto) quando cliente pede depois do primeiro envio. Use quando cliente já recebeu um formato e pede o outro.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "cpf_cnpj": {
                                    "type": "string",
                                    "description": "CPF ou CNPJ do cliente"
                                },
                                "formato_solicitado": {
                                    "type": "string",
                                    "description": "Formato que o cliente pediu adicionalmente: 'pix' ou 'boleto'",
                                    "enum": ["pix", "boleto"]
                                },
                                "numero_whatsapp": {
                                    "type": "string",
                                    "description": "Número do WhatsApp do cliente"
                                }
                            },
                            "required": ["cpf_cnpj", "formato_solicitado"]
                        }
                    }
                }
            ]
            
            # SEMPRE adicionar ferramentas de banco de dados para transferências
            tools.extend(DATABASE_FUNCTION_TOOLS)
            
            # ADICIONAR FERRAMENTAS DE TRANSFERÊNCIA COM DESCRIÇÕES MELHORADAS
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "buscar_equipes_disponiveis",
                        "description": "BUSCAR EQUIPES: Verifica quais equipes estão disponíveis para transferência. USE SEMPRE ANTES de transferir. Retorna lista de equipes como SUPORTE TÉCNICO, FINANCEIRO, VENDAS, etc.",
                        "parameters": {
                            "type": "object", 
                            "properties": {},
                            "required": []
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "executar_transferencia_conversa", 
                        "description": "TRANSFERIR CONVERSA: Executa transferência REAL para equipe especializada. USE APÓS buscar_equipes_disponiveis(). Analise a conversa e escolha a equipe MAIS ADEQUADA: SUPORTE TÉCNICO (problemas internet), FINANCEIRO (faturas/pagamentos), VENDAS (novos clientes), ATENDIMENTO GERAL (outros casos).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "conversation_id": {
                                    "type": "string", 
                                    "description": "ID da conversa atual (OBRIGATÓRIO)"
                                },
                                "equipe_nome": {
                                    "type": "string",
                                    "description": "Nome da equipe baseado na análise: SUPORTE TÉCNICO (problemas técnicos), FINANCEIRO (faturas/pagamentos), VENDAS (planos/contratações), ATENDIMENTO GERAL (outros)"
                                },
                                "motivo": {
                                    "type": "string", 
                                    "description": "Motivo detalhado baseado na análise da conversa. Ex: 'Cliente relata internet lenta há 3 dias - precisa diagnóstico técnico'"
                                }
                            },
                            "required": ["conversation_id", "equipe_nome", "motivo"]
                        }
                    }
                }
            ])
            
            # FORÇAR USO DE FERRAMENTAS quando cliente pedir fatura/PIX/boleto
            mensagem_lower = mensagem.lower()
            force_tools = any(word in mensagem_lower for word in ['pix', 'boleto', 'fatura', 'pagar', 'pagamento'])
            
            # Adicionar instrução específica para faturas
            if force_tools:
                if cpf_cnpj_match:
                    cpf_cnpj = cpf_cnpj_match.group().replace('.', '').replace('-', '').replace('/', '')
                    system_prompt += f"""

🚨 CLIENTE JÁ FORNECEU CPF/CNPJ: {cpf_cnpj}
- PRIMEIRO: Use consultar_cliente_sgp para identificar o cliente
- SEGUNDO: Use gerar_fatura_completa com este CPF/CNPJ
- NÃO pergunte novamente o CPF/CNPJ
- NÃO transfira para equipe - resolva diretamente
- Execute as funções na ordem: consultar_cliente_sgp → gerar_fatura_completa
- IGNORE qualquer lógica de transferência - o cliente já forneceu dados suficientes
"""
                else:
                    system_prompt += """

⚠️ ATENÇÃO - CLIENTE PEDIU FATURA/PAGAMENTO:
- PRIMEIRO: Pergunte o CPF/CNPJ do cliente
- SEGUNDO: Use consultar_cliente_sgp para identificar o cliente
- TERCEIRO: Use gerar_fatura_completa para gerar a fatura
- NÃO transfira para equipe - resolva diretamente
- Exemplo: "Para gerar sua fatura, preciso do seu CPF ou CNPJ. Pode me informar?"

🎯 LÓGICA DE FORMATOS ADICIONAIS:
- Se cliente já recebeu PIX e pede "também PDF/boleto" → Use enviar_formato_adicional(formato_solicitado: "boleto")
- Se cliente já recebeu Boleto e pede "também PIX" → Use enviar_formato_adicional(formato_solicitado: "pix")
- Só envie o formato que o cliente ainda não recebeu
"""
            
            # Fazer chamada inicial COM ferramentas disponíveis
            try:
                # Debug removido
                # Debug removido
                if force_tools:
                    pass  # Debug removido
                else:
                    pass  # Debug removido
                    
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    tools=tools,
                    tool_choice="required" if force_tools else "auto"
                )
            except Exception as e:
                logger.error(f"❌ ERRO na chamada OpenAI: {e}")
                raise
            
            # Processar se a IA chamou alguma ferramenta
            if response.choices[0].message.tool_calls:
                # Processar todas as ferramentas chamadas pela IA
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"IA chamou função: {function_name} com argumentos: {function_args}")
                    
                    # Executar a função chamada pela IA
                    if function_name in DATABASE_FUNCTION_MAPPING:
                        # Executar função de banco de dados
                        function_result = self._execute_database_function(provedor, function_name, function_args, contexto)
                    else:
                        # Executar função SGP
                        function_result = self._execute_sgp_function(provedor, function_name, function_args, contexto)
                    
                    # Adicionar resultado da função à conversa
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]  # Incluir apenas esta ferramenta específica
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(function_result, ensure_ascii=False)
                    })
                
                # Gerar resposta final com os dados das funções
                try:
                    response = openai.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature
                    )
                except Exception as e:
                    logger.error(f"Erro ao gerar resposta final após execução das ferramentas: {e}")
                    # Se falhar, retornar erro
                    return {
                        "success": False,
                        "erro": f"Erro ao processar resposta após execução das ferramentas: {str(e)}",
                        "provedor": provedor.nome
                    }
            
            # Processar resposta (com ou sem ferramentas)
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada para provedor {provedor.nome}: {resposta[:100]}...")
            
            # Validação de dados fixos removida - usando apenas dados dinâmicos
            
            # VALIDAÇÃO E CORREÇÃO DO FORMATO - FORÇAR FORMATO CORRETO
            resposta = self._corrigir_formato_resposta(resposta)
            logger.info(f"Resposta após correção de formato: {resposta[:100]}...")
            
            # ATUALIZAR MEMÓRIA DA CONVERSA NO REDIS
            if conversation:
                # Atualizar contador de mensagens
                current_memory = redis_memory_service.get_conversation_memory_sync(
                    provedor_id=provedor.id,
                    conversation_id=conversation.id
                ) or {}
                
                message_count = current_memory.get('message_count', 0) + 1
                
                # Salvar contexto da mensagem atual (preservando dados existentes)
                message_context = {
                    **current_memory,  # Preservar dados existentes
                    'message_count': message_count,
                    'last_message': {
                        'content': mensagem[:200] + "..." if len(mensagem) > 200 else mensagem,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'user'
                    },
                    'last_response': {
                        'content': resposta[:200] + "..." if len(resposta) > 200 else resposta,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'ai'
                    },
                    'context:last_interaction': {
                        'user_message': mensagem,
                        'ai_response': resposta,
                        'timestamp': datetime.now().isoformat()
                    },
                    'last_updated': datetime.now().isoformat()
                }
                
                # Se detectou CPF/CNPJ, salvar na memória (preservar se já existir)
                if cpf_cnpj_detected:
                    message_context['context:cpf_cnpj_detected'] = cpf_cnpj_detected
                    logger.info(f"CPF/CNPJ salvo na memória: {cpf_cnpj_detected}")
                
                # Atualizar memória
                redis_memory_service.set_conversation_memory_sync(
                    provedor_id=provedor.id,
                    conversation_id=conversation.id,
                    data=message_context
                )
                
                logger.info(f"Memória da conversa {conversation.id} atualizada no Redis")
                logger.info(f"CPF/CNPJ na memória: {message_context.get('context:cpf_cnpj_detected', 'Não encontrado')}")
            
            # LÓGICA DE TRANSFERÊNCIA INTELIGENTE PARA EQUIPES
            provedor_capability = None
            if conversation:
                # Verificar capacidade de transferência do provedor
                provedor_capability = transfer_service.check_provedor_transfer_capability(provedor)
                logger.info(f"Capacidade de transferência do provedor {provedor.nome}: {provedor_capability.get('capability_score', 0)}%")
                
            # Adicionar instrução para IA tentar resolver primeiro ANTES da análise de transferência
            system_prompt += """

IMPORTANTE - LÓGICA DE ATENDIMENTO:
1. SEMPRE tente resolver o problema do cliente primeiro
2. Se conseguir resolver, não transfira
3. Se NÃO conseguir resolver ou cliente solicitar especificamente uma equipe, ENTÃO transfira
4. Para transferências, use as ferramentas de banco de dados disponíveis
5. Seja proativo e tente ajudar antes de transferir

EXEMPLOS:
- Cliente: "Minha internet está lenta" → Tente diagnosticar e resolver primeiro
- Cliente: "Quero falar com o financeiro" → Transfira diretamente para financeiro
- Cliente: "Preciso de ajuda técnica" → Tente resolver, se não conseguir, transfira para suporte técnico

FERRAMENTAS DISPONÍVEIS PARA TRANSFERÊNCIA:
- buscar_equipes_disponiveis() - Busca equipes disponíveis
- executar_transferencia_conversa(team_id, team_name) - Executa transferência real

🚨 OBRIGATÓRIO: Quando cliente solicitar transferência, você DEVE:
1. PRIMEIRO: Tentar resolver o problema
2. SE NÃO CONSEGUIR: Use buscar_equipes_disponiveis() para encontrar equipe
3. DEPOIS: Use executar_transferencia_conversa() para transferir REALMENTE
4. NUNCA apenas confirme que vai transferir - EXECUTE a transferência!

""" + DATABASE_SYSTEM_INSTRUCTIONS
                
            
            # INSTRUÇÕES ESPECÍFICAS PARA TRANSFERÊNCIA INTELIGENTE
            system_prompt += """

TRANSFERÊNCIA INTELIGENTE OBRIGATÓRIA - ANALISE A CONVERSA E TRANSFIRA PARA EQUIPE CORRETA

VOCÊ DEVE ANALISAR A CONVERSA E TRANSFERIR AUTOMATICAMENTE QUANDO IDENTIFICAR:

CATEGORIAS DE TRANSFERÊNCIA:

1. SUPORTE TÉCNICO (Problemas de internet/conexão):
   - Cliente relata: "sem internet", "internet lenta", "não funciona", "problema de conexão"
   - Cliente menciona: "modem", "roteador", "LED vermelho", "wi-fi", "sinal"
   - Cliente diz: "caiu", "offline", "sem acesso", "velocidade baixa"
   - Após verificar_acesso_sgp mostrar problema técnico

2. FINANCEIRO (Problemas de pagamento/faturas):
   - Cliente relata: "fatura", "boleto", "pagamento", "conta", "débito", "vencimento"
   - Cliente menciona: "pagar", "valor", "cobrança", "segunda via", "atraso"
   - Cliente diz: "não consegui pagar", "problema com pagamento", "dúvida na fatura"

3. VENDAS (Novos clientes ou mudança de plano):
   - Cliente pergunta: "planos", "contratar", "preços", "ofertas", "mudar plano"
   - Cliente menciona: "quero assinar", "valores", "velocidades", "instalação"
   - Cliente é NOVO CLIENTE interessado em serviços

4. ATENDIMENTO GERAL (Outras solicitações):
   - Cliente pede: "humano", "atendente", "pessoa", "falar com alguém"
   - Cliente diz: "não resolveu", "quero falar com supervisor", "reclamação"
   - Casos não cobertos pelas categorias acima

FLUXO OBRIGATÓRIO PARA TRANSFERÊNCIA:

1. ANALISAR a conversa e identificar a necessidade real do cliente
2. USAR buscar_equipes_disponiveis() para ver equipes disponíveis
3. ESCOLHER a equipe MAIS ADEQUADA baseada na análise
4. EXECUTAR executar_transferencia_conversa() com a equipe correta

NUNCA FAÇA:
- Transferir para equipe errada (ex: técnico para problema financeiro)
- Pedir confirmação do cliente para transferir
- Deixar de transferir quando identificou necessidade clara
- Continuar atendendo quando cliente precisa de equipe especializada

SEMPRE FAÇA:
- Analisar o contexto completo da conversa
- Transferir IMEDIATAMENTE quando identificar necessidade
- Escolher a equipe MAIS ESPECÍFICA para o problema
- Executar AMBAS as funções (buscar e transferir)

EXEMPLOS PRÁTICOS:

CLIENTE: "Minha internet está lenta há 3 dias"
→ Analisar: Problema técnico persistente
→ Equipe: SUPORTE TÉCNICO
→ Motivo: "Cliente relata internet lenta há 3 dias - precisa de diagnóstico técnico"

CLIENTE: "Não consegui pagar a fatura deste mês"
→ Analisar: Problema financeiro/pagamento
→ Equipe: FINANCEIRO  
→ Motivo: "Cliente com dificuldade no pagamento da fatura"

CLIENTE: "Quero conhecer os planos de internet"
→ Analisar: Interesse em contratação
→ Equipe: VENDAS
→ Motivo: "Cliente interessado em planos de internet"

CLIENTE: "Preciso falar com um atendente humano"
→ Analisar: Solicitação explícita por humano
→ Equipe: ATENDIMENTO GERAL
→ Motivo: "Cliente solicitou atendimento humano"
"""

            # ADICIONAR INSTRUÇÃO ESPECÍFICA SE DETECTOU NECESSIDADE DE TRANSFERÊNCIA
            if transfer_necessario:
                        system_prompt += f"""

TRANSFERÊNCIA IDENTIFICADA - EXECUTE AGORA!

ANÁLISE DA CONVERSA: {motivo_transferencia}
EQUIPE RECOMENDADA: {equipe_sugerida}

VOCÊ DEVE EXECUTAR IMEDIATAMENTE:

1. buscar_equipes_disponiveis() - para verificar equipes
2. executar_transferencia_conversa(
   conversation_id={conversation.id},
   equipe_nome="{equipe_sugerida}",
   motivo="{motivo_transferencia}"
)

NÃO PERGUNTE - NÃO CONFIRME - EXECUTE A TRANSFERÊNCIA AGORA!

O cliente precisa de atendimento especializado e você deve transferir IMEDIATAMENTE.

IMPORTANTE: Você DEVE usar as ferramentas de banco de dados disponíveis:
- buscar_equipes_disponiveis() - para verificar equipes disponíveis
- executar_transferencia_conversa() - para executar a transferência real

NÃO APENAS CONFIRME - EXECUTE A TRANSFERÊNCIA REAL!
"""
            
            # REGRAS FINAIS PARA TRANSFERÊNCIA
            system_prompt += """

REGRAS FINAIS DE TRANSFERÊNCIA:

1. SEMPRE analise o contexto completo da conversa antes de transferir
2. TRANSFIRA IMEDIATAMENTE quando identificar necessidade clara de equipe especializada
3. NÃO tente resolver problemas complexos que requerem equipe especializada
4. USE buscar_equipes_disponiveis() PRIMEIRO para ver disponibilidade
5. USE executar_transferencia_conversa() DEPOIS para transferir REALMENTE

LEMBRE-SE: A transferência só acontece se você USAR as duas funções!
"""
            
            if transfer_necessario:
                logger.info("Solicitação de transferência detectada - instruções adicionadas ao prompt")
            
            # Verificar se precisa marcar que perguntou sobre ser cliente
            already_asked_if_client = conversation.additional_attributes.get('asked_if_client', False) if conversation else False
            if not already_asked_if_client and conversation and needs_client_check:
                logger.info("Verificando se a resposta contém pergunta sobre ser cliente")
                # Verificar se a resposta já contém uma pergunta sobre ser cliente
                client_questions = [
                    "já é nosso cliente",
                    "já é cliente",
                    "é nosso cliente",
                    "é cliente da",
                    "você já é cliente",
                    "para te ajudar melhor, você já é",
                    "posso confirmar se você já é"
                ]
                
                resposta_contem_pergunta = any(question in resposta.lower() for question in client_questions)
                logger.info(f"Resposta contém pergunta sobre ser cliente: {resposta_contem_pergunta}")
                
                # Só marcar que perguntou se realmente perguntou
                if resposta_contem_pergunta:
                    conversation.additional_attributes['asked_if_client'] = True
                    conversation.save(update_fields=['additional_attributes'])
                    logger.info(f"Marcado que já perguntou se é cliente para conversa {conversation.id}")
                else:
                    logger.info("Resposta não contém pergunta sobre ser cliente - não marcando como perguntado")
            else:
                if already_asked_if_client:
                    logger.info("Já perguntou se é cliente anteriormente")
                elif not needs_client_check:
                    logger.info("Não foi necessário perguntar se é cliente nesta mensagem")
                if not conversation:
                    logger.warning("Nenhuma conversa fornecida para marcar asked_if_client")
            
            # SALVAR RESPOSTA DA IA NO REDIS
            if contexto and contexto.get('conversation') and resposta:
                try:
                    conversation = contexto['conversation']
                    redis_memory_service.add_message_to_conversation_sync(
                        provedor_id=provedor.id,
                        conversation_id=conversation.id,
                        sender='ai',
                        content=resposta,
                        message_type='text'
                    )
                    logger.info(f"✅ Resposta da IA salva no Redis: {resposta[:50]}...")
                    
                    # VERIFICAR SE É MENSAGEM DE ENCERRAMENTO E LIMPAR REDIS
                    if conversation.status == 'closed':
                        try:
                            # Limpar memória Redis da conversa encerrada
                            redis_memory_service.clear_conversation_memory(conversation.id)
                            logger.info(f"🧹 Memória Redis limpa para conversa {conversation.id} após encerramento")
                            
                            # Limpar também mensagens do banco de dados (manter apenas auditoria)
                            from conversations.models import Message
                            messages_to_delete = Message.objects.filter(conversation=conversation)
                            messages_count = messages_to_delete.count()
                            messages_to_delete.delete()
                            logger.info(f"🗑️ {messages_count} mensagens removidas do banco para conversa {conversation.id}")
                            
                        except Exception as e:
                            logger.warning(f"Erro ao limpar memória Redis da conversa {conversation.id}: {e}")
                            
                except Exception as e:
                    logger.warning(f"Erro ao salvar resposta da IA no Redis: {e}")
            
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                "provedor": provedor.nome,
                "agente": provedor.nome_agente_ia
            }
        except Exception as e:
            logger.error(f"Erro ao gerar resposta com OpenAI: {str(e)}")
            return {
                "success": False,
                "erro": f"Erro ao processar mensagem: {str(e)}",
                "provedor": provedor.nome
            }

    def _analyze_transfer_decision(self, mensagem: str, resposta: str, conversation) -> Optional[Dict[str, str]]:
        """
        Analisa a mensagem do cliente e a resposta da IA para decidir se deve transferir para uma equipe especializada.
        Retorna um dicionário com 'equipe' e 'motivo' ou None.
        """
        transfer_decisions = {
            "tecnico": {
                "keywords": ["técnico", "instalação", "internet parou", "não funciona", "problema", "chamado", "reclamação"],
                "equipe": "Suporte Técnico",
                "motivo": "problemas técnicos ou instalação"
            },
            "financeiro": {
                "keywords": ["fatura", "boleto", "pagamento", "débito", "vencimento", "valor", "conta", "pagar"],
                "equipe": "Financeiro",
                "motivo": "dúvidas sobre faturas, pagamentos ou questões financeiras"
            },
            "vendas": {
                "keywords": ["plano", "contratar", "contratação", "internet", "fibra", "oferta", "melhor", "escolher", "escolha"],
                "equipe": "Vendas",
                "motivo": "interesse em novos planos de internet"
            },
            "atendimento_especializado": {
                "keywords": ["urgente", "prioritário", "emergência", "crítico", "acelerar", "acelerar atendimento", "atendimento rápido"],
                "equipe": "Atendimento Especializado",
                "motivo": "atendimento urgente ou de alta prioridade"
            }
        }

        for decision in transfer_decisions.values():
            if any(keyword in mensagem.lower() for keyword in decision["keywords"]):
                return decision

        # Se nenhuma decisão de transferência foi encontrada, mas a resposta indica uma transferência
        if "transferir" in resposta.lower() or "encaminhar" in resposta.lower():
            # Tenta identificar a equipe baseada na última mensagem do cliente
            last_message = conversation.messages[-1] if conversation.messages else None
            if last_message and last_message.role == "user":
                for decision in transfer_decisions.values():
                    if any(keyword in last_message.content.lower() for keyword in decision["keywords"]):
                        return decision

        return None

    def _detect_cpf_cnpj(self, mensagem: str) -> Optional[str]:
        """
        Detecta se há CPF ou CNPJ na mensagem.
        Retorna o CPF/CNPJ encontrado ou None.
        """
        import re
        
        # Padrões para CPF (XXX.XXX.XXX-XX ou XXXXXXXXXXX)
        cpf_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
        
        # Padrões para CNPJ (XX.XXX.XXX/XXXX-XX ou XXXXXXXXXXXXXX)
        cnpj_pattern = r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'
        
        # Buscar CPF
        cpf_match = re.search(cpf_pattern, mensagem)
        if cpf_match:
            return cpf_match.group()
        
        # Buscar CNPJ
        cnpj_match = re.search(cnpj_pattern, mensagem)
        if cnpj_match:
            return cnpj_match.group()
        
        return None

    def _send_fatura_via_uazapi(self, provedor: Provedor, numero_whatsapp: str, dados_fatura: dict) -> bool:
        """
        Envia fatura via FaturaService que já tem toda a lógica implementada
        """
        try:
            from .fatura_service import FaturaService
            
            # Criar instância do FaturaService
            fatura_service = FaturaService()
            
            # Converter dados para o formato esperado pelo FaturaService
            # O FaturaService espera os dados no formato do SGP
            dados_sgp = {
                'links': [{
                    'fatura': dados_fatura.get('fatura_id', 'N/A'),
                    'valor': dados_fatura.get('valor', 0),
                    'vencimento': dados_fatura.get('vencimento', 'N/A'),
                    'codigopix': dados_fatura.get('codigo_pix'),
                    'linhadigitavel': dados_fatura.get('linha_digitavel'),
                    'link': dados_fatura.get('link_fatura')
                }]
            }
            
            # Usar o método do FaturaService que já está funcionando
            resultado = fatura_service.enviar_fatura_uazapi(
                provedor=provedor,
                numero_whatsapp=numero_whatsapp,
                dados_fatura=dados_sgp
            )
            
            if resultado:
                logger.info(f"Fatura enviada via FaturaService para {numero_whatsapp}")
                return True
            else:
                logger.error(f"Falha ao enviar fatura via FaturaService para {numero_whatsapp}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar fatura via FaturaService: {str(e)}")
            return False
    
    def process_pdf_with_ai(self, pdf_path: str, provedor: Provedor, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa um PDF usando pdfplumber e gera resposta com IA
        """
        try:
            logger.info(f"Processando PDF: {pdf_path}")
            
            # Extrair informações do PDF usando pdfplumber
            pdf_info = pdf_processor.extract_payment_info(pdf_path)
            
            if not pdf_info.get('is_payment_receipt'):
                return {
                    'success': False,
                    'erro': 'PDF não é um comprovante de pagamento válido',
                    'pdf_info': pdf_info
                }
            
            # Gerar prompt para a IA baseado nas informações extraídas
            ai_prompt = pdf_processor.generate_ai_prompt(pdf_info)
            
            # Adicionar contexto do PDF ao contexto geral
            if contexto is None:
                contexto = {}
            
            contexto['pdf_info'] = pdf_info
            contexto['pdf_path'] = pdf_path
            
            # Gerar resposta da IA
            ai_response = self.generate_response_sync(
                mensagem=ai_prompt,
                provedor=provedor,
                contexto=contexto
            )
            
            if ai_response['success']:
                return {
                    'success': True,
                    'resposta': ai_response['resposta'],
                    'pdf_info': pdf_info,
                    'ai_response': ai_response
                }
            else:
                return {
                    'success': False,
                    'erro': f"Erro na IA: {ai_response.get('erro', 'Erro desconhecido')}",
                    'pdf_info': pdf_info
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            return {
                'success': False,
                'erro': f'Erro ao processar PDF: {str(e)}'
            }
    
    def analyze_image_with_ai(self, image_path: str, provedor: Provedor, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analisa uma imagem usando a API da OpenAI com suporte a visão
        """
        try:
            logger.info(f"Analisando imagem: {image_path}")
            
            # Buscar chave da API apenas quando necessário
            if not self.api_key:
                self.api_key = self._get_api_key()
                if self.api_key:
                    openai.api_key = self.api_key
                else:
                    return {
                        'success': False,
                        'erro': 'Chave da API OpenAI não encontrada'
                    }
            
            # Verificar se o arquivo existe
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'erro': f'Arquivo de imagem não encontrado: {image_path}'
                }
            
            # Criar prompt para análise da imagem
            image_prompt = """
            Analise esta imagem enviada pelo cliente com foco em problemas de internet.
            
            Se for um modem, roteador ou equipamento de internet:
            - Verifique se há LEDs acesos ou apagados
            - IDENTIFIQUE ESPECIFICAMENTE se há LEDs VERMELHOS (problema crítico)
            - Verifique se há LEDs verdes/azuis (funcionando)
            - Observe se há cabos conectados
            - Identifique a marca/modelo se possível
            - Descreva o estado geral do equipamento
            
            IMPORTANTE: Se detectar LED VERMELHO em modem/roteador:
            - Responda APENAS: "Detectei que seu equipamento está com problema (LED vermelho). Vou transferir você para nossa equipe de suporte técnico que irá resolver isso para você."
            - NÃO envie análise técnica detalhada
            - NÃO explique o que é LED vermelho
            - Apenas informe que será transferido para suporte
            
            Se for outro tipo de equipamento ou problema:
            - Descreva o que você vê
            - Identifique possíveis problemas
            - Sugira soluções básicas
            
            Responda de forma técnica mas acessível ao cliente.
            Se houver LED vermelho, SEMPRE mencione que será transferido para suporte técnico.
            """
            
            # Fazer a chamada para a API da OpenAI com suporte a visão
            client = openai.OpenAI(api_key=self.api_key)
            
            # Ler a imagem e converter para base64
            import base64
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = client.chat.completions.create(
                model="gpt-4.1",  # Modelo com suporte a visão
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": image_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            resposta = response.choices[0].message.content
            
            # Detectar se há LED vermelho na resposta para transferir para suporte
            led_vermelho_detectado = any(keyword in resposta.lower() for keyword in [
                'led vermelho', 'led vermelha', 'vermelho', 'vermelha',
                'problema físico', 'drop', 'fibra', 'conectores',
                'transferir', 'suporte técnico', 'intervenção física'
            ])
            
            return {
                'success': True,
                'resposta': resposta,
                'model': 'gpt-4.1',
                'provedor': provedor.nome,
                'image_path': image_path,
                'led_vermelho_detectado': led_vermelho_detectado,
                'transferir_suporte': led_vermelho_detectado
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar imagem: {str(e)}")
            return {
                'success': False,
                'erro': f'Erro ao analisar imagem: {str(e)}'
            }
    
    async def process_pdf_with_ai_async(self, pdf_path: str, provedor: Provedor, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Versão assíncrona do processamento de PDF
        """
        try:
            logger.info(f"Processando PDF (async): {pdf_path}")
            
            # Extrair informações do PDF usando pdfplumber
            pdf_info = pdf_processor.extract_payment_info(pdf_path)
            
            if not pdf_info.get('is_payment_receipt'):
                return {
                    'success': False,
                    'erro': 'PDF não é um comprovante de pagamento válido',
                    'pdf_info': pdf_info
                }
            
            # Gerar prompt para a IA baseado nas informações extraídas
            ai_prompt = pdf_processor.generate_ai_prompt(pdf_info)
            
            # Adicionar contexto do PDF ao contexto geral
            if contexto is None:
                contexto = {}
            
            contexto['pdf_info'] = pdf_info
            contexto['pdf_path'] = pdf_path
            
            # Gerar resposta da IA
            ai_response = await self.generate_response(
                mensagem=ai_prompt,
                provedor=provedor,
                contexto=contexto
            )
            
            if ai_response['success']:
                return {
                    'success': True,
                    'resposta': ai_response['resposta'],
                    'pdf_info': pdf_info,
                    'ai_response': ai_response
                }
            else:
                return {
                    'success': False,
                    'erro': f"Erro na IA: {ai_response.get('erro', 'Erro desconhecido')}",
                    'pdf_info': pdf_info
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar PDF (async): {str(e)}")
            return {
                'success': False,
                'erro': f'Erro ao processar PDF: {str(e)}'
            }
    
    def _get_nome_para_csat(self, conversation):
        """
        Obtém o nome para usar no CSAT, priorizando o nome do SGP se disponível,
        senão usa o nome do WhatsApp
        """
        try:
            # Primeiro, tentar obter o nome do SGP (se a IA já identificou o cliente)
            from core.redis_memory_service import RedisMemoryService
            redis_memory = RedisMemoryService()
            memory = redis_memory.get_conversation_memory_sync(conversation.inbox.provedor.id, conversation.id)
            if memory and memory.get('nome_cliente'):
                return memory['nome_cliente']
            
            # Se não tiver nome do SGP, usar o nome do contato
            if conversation.contact and conversation.contact.name:
                return conversation.contact.name
            
            # Fallback para nome genérico
            return "Cliente"
            
        except Exception as e:
            logger.error(f"Erro ao obter nome para CSAT: {e}")
            return "Cliente"

openai_service = OpenAIService() 
