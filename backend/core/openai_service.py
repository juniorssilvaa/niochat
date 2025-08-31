"""
Serviço para integração com OpenAI ChatGPT
"""

import os
import openai
import logging
import json
import re
from typing import Dict, Any, Optional, List
from django.conf import settings
from .models import Provedor, SystemConfig
from asgiref.sync import sync_to_async
from datetime import datetime
from .redis_memory_service import redis_memory_service
from .transfer_service import transfer_service

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
        if any(termo in resposta for termo in ['*Dados do Cliente:*', '*Nome:*', '*Status do Contrato:*', 'ℹ', '👤', '🔒']):
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
                resultado = sgp.verifica_acesso(contrato)
                
                status_conexao = (
                    resultado.get('msg') or
                    resultado.get('status') or 
                    resultado.get('status_conexao') or
                    resultado.get('mensagem') or
                    "Status não disponível"
                )
                
                return {
                    "success": True,
                    "contrato": contrato,
                    "status_conexao": status_conexao,
                    "dados_completos": resultado
                }
                
            elif function_name == "encerrar_atendimento":
                # Implementação para encerrar atendimento e limpar memória
                try:
                    motivo = function_args.get('motivo', 'nao_especificado')
                    
                    # Limpar memória Redis da conversa se disponível
                    conversation_id = None
                    if contexto and contexto.get('conversation'):
                        conversation_id = contexto['conversation'].id
                        
                        try:
                            # Limpar memória Redis
                            from .redis_memory_service import redis_memory_service
                            redis_client = redis_memory_service.get_redis_sync()
                            if redis_client and conversation_id:
                                chave_conversa = f'conversation:{provedor.id}:{conversation_id}'
                                redis_client.delete(chave_conversa)
                                logger.info(f"Memória Redis limpa para conversa {conversation_id}")
                        except Exception as e:
                            logger.warning(f"Erro ao limpar memória Redis: {e}")
                    
                    return {
                        "success": True,
                        "atendimento_encerrado": True,
                        "motivo": motivo,
                        "mensagem": "Obrigado pelo contato! Tenha um ótimo dia! 👋",
                        "conversation_id": conversation_id
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
                        
                        # O SGP aceita CPF/CNPJ diretamente - não precisa buscar contrato_id primeiro
                        # Processar fatura completa usando FaturaService com CPF/CNPJ
                        resultado = fatura_service.processar_fatura_completa(
                            provedor=provedor,
                            cpf_cnpj=cpf_cnpj,  # Usar CPF/CNPJ diretamente
                            numero_whatsapp=numero_whatsapp,
                            preferencia_pagamento=tipo_pagamento,  # PIX ou boleto conforme solicitado
                            conversation=contexto.get('conversation')
                        )
                        
                        if resultado.get('success'):
                            # Criar mensagem dinâmica baseada no tipo de pagamento
                            if tipo_pagamento == 'pix':
                                mensagem_sucesso = "✅ Acabei de enviar sua fatura via WhatsApp com QR Code e botão de cópia PIX!\n\nPosso te ajudar com mais alguma coisa?"
                            else:  # boleto
                                mensagem_sucesso = "✅ Acabei de enviar sua fatura via WhatsApp com boleto PDF!\n\nPosso te ajudar com mais alguma coisa?"
                            
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
                
            elif function_name == "enviar_qr_code_pix":
                # Implementação para enviar apenas QR Code PIX
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
                    "fatura_id": fatura_id,
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

            # NOVO PROMPT COMPLETO E PROFISSIONAL
            system_prompt = f"""
IMPORTANTE: Sempre retorne as mensagens em uma lista (um bloco para cada mensagem), para que o frontend exiba cada uma separadamente com efeito de 'digitando...'. Nunca junte mensagens diferentes em um único bloco.

Você é {provedor.nome_agente_ia}, agente virtual do provedor {provedor.nome}. Seu papel é atender clientes e interessados, oferecendo suporte técnico, esclarecendo dúvidas e apresentando planos de internet. Seja acolhedor, objetivo e resolva o que for possível.{historico_conversa}

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

MEMÓRIA DE CONTEXTO (REDIS):
- USE A MEMÓRIA REDIS PARA LEMBRAR DO QUE JÁ FOI CONVERSADO
- SE JÁ CONSULTOU O CLIENTE, NÃO PEÇA CPF/CNPJ NOVAMENTE
- SE CLIENTE JÁ ESCOLHEU PIX/BOLETO, USE gerar_fatura_completa IMEDIATAMENTE
- QUANDO CLIENTE PEDIR "PAGA FATURA" E JÁ TEM CPF, EXECUTE gerar_fatura_completa
- NUNCA REPITA PERGUNTAS JÁ FEITAS
- LEMBRE-SE DO QUE JÁ FOI CONVERSADO

FLUXO FATURA SIMPLIFICADO:
1. Cliente pede fatura/PIX/boleto
2. Use gerar_fatura_completa com CPF/CNPJ do cliente (da memória Redis) e número do WhatsApp
3. A função faz TUDO automaticamente: SGP + QR Code + WhatsApp + Botões + Mensagem de confirmação
4. NÃO mostre dados da fatura manualmente - a função já faz isso
5. NÃO confirme novamente - a função já confirma
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
            tools = [
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
                        "description": "OBRIGATÓRIO: Esta é a ÚNICA forma de gerar faturas. Use sua inteligência para interpretar se o cliente prefere PIX (rápido/instantâneo) ou boleto (tradicional/físico). NUNCA mostre dados fixos. SEMPRE use esta função quando cliente pedir fatura ou pagamento.",
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
                        "description": "Verificar status da conexão do cliente. Use quando cliente relatar problemas de internet.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "contrato": {"type": "string", "description": "ID do contrato"}
                            },
                            "required": ["contrato"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "encerrar_atendimento",
                        "description": "OBRIGATÓRIO: Use quando cliente disser 'não', 'não preciso', 'tá bom', 'obrigado' ou qualquer resposta indicando que não precisa de mais ajuda. Limpa a memória Redis e encerra o atendimento.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "motivo": {"type": "string", "description": "Motivo do encerramento (ex: 'cliente_satisfeito', 'nao_precisa_mais')"}
                            },
                            "required": ["motivo"]
                        }
                    }
                }
            ]
            
            # Detectar se cliente pediu fatura/pagamento
            mensagem_lower = mensagem.lower()
            cliente_pediu_fatura = any(word in mensagem_lower for word in ['paga', 'fatura', 'pix', 'boleto', 'pagamento', 'pagar'])
            
            # Se cliente pediu fatura, adicionar instrução específica
            if cliente_pediu_fatura:
                system_prompt += """

🚨 CLIENTE PEDIU FATURA/PAGAMENTO:
- IMPORTANTE: Antes de usar gerar_fatura_completa, você DEVE perguntar o CPF/CNPJ do cliente
- Só use gerar_fatura_completa quando tiver o CPF/CNPJ válido (11 ou 14 dígitos)
- Se cliente não informou CPF/CNPJ, pergunte: "Qual é o seu CPF ou CNPJ?"
- Use gerar_fatura_completa apenas com dados válidos:
  * cpf_cnpj: CPF/CNPJ completo e válido (11 ou 14 dígitos)
  * tipo_pagamento: "pix" ou "boleto" baseado na intenção do cliente
- A função faz TUDO automaticamente: SGP + envio via WhatsApp + Mensagem específica
- NÃO envie mensagens adicionais - a função já confirma tudo
"""
            
            # Forçar uso de ferramentas quando necessário
            force_tools = any(word in mensagem_lower for word in ['pix', 'boleto', 'fatura', 'pagar'])
            
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
                    function_result = self._execute_sgp_function(provedor, function_name, function_args, contexto)
                    
                    # Salvar informações importantes na memória Redis
                    if conversation_id and function_result.get('success'):
                        memory_updates = {}
                        
                        # Salvar dados do cliente se foi consultado
                        if function_name == "consultar_cliente_sgp":
                            if function_result.get('nome'):
                                memory_updates['nome_cliente'] = function_result['nome']
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
                    resposta = "❌ Erro interno: Preciso consultar o sistema primeiro. Me informe seu CPF/CNPJ para buscar seus dados reais."
                    break
            
            return {
                "success": True,
                "resposta": resposta,
                "model": self.model,
                "provedor": provedor.nome
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
- ❌ NUNCA: "ℹ *Dados do Cliente:*"
- ❌ NUNCA use nomes fixos - SEMPRE use dados reais do SGP
- ❌ NUNCA: "🔒 *Status do Contrato:* Suspenso"
- ❌ NUNCA: "*Cliente Encontrado*"
- ❌ NUNCA: "Como posso te ajudar hoje, Pedro?"

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
                        "description": "Consulta dados reais do cliente no SGP usando CPF/CNPJ. SEMPRE use esta ferramenta quando receber CPF/CNPJ. FORMATO OBRIGATÓRIO: Para UM contrato use 'Contrato:' seguido de '*NOME*' e '1 - Contrato (ID): *ENDEREÇO*'. Para MÚLTIPLOS contratos use 'Contratos:' seguido da lista. NUNCA use emojis ℹ 👤 🔒 ou frases como 'Cliente Encontrado', 'Nome:', 'Status do Contrato:'.",
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
                        "description": "Verifica status de acesso/conexão de um contrato no SGP. Use após identificar o contrato do cliente. IMPORTANTE: Formate a resposta EXATAMENTE assim: 📡 *Status do seu acesso:* seguido de Status e Contrato.",
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
                }
            ]
            
            # FORÇAR USO DE FERRAMENTAS quando cliente pedir fatura/PIX/boleto
            mensagem_lower = mensagem.lower()
            force_tools = any(word in mensagem_lower for word in ['pix', 'boleto', 'fatura', 'pagar', 'pagamento'])
            
            # Adicionar instrução específica para faturas
            if force_tools:
                system_prompt += """

⚠️ ATENÇÃO - CLIENTE PEDIU FATURA/PAGAMENTO:
- ANTES de usar qualquer ferramenta de fatura, você DEVE perguntar o CPF/CNPJ
- Exemplo: "Para gerar sua fatura, preciso do seu CPF ou CNPJ. Pode me informar?"
- Só use gerar_fatura_completa quando tiver um CPF/CNPJ válido (11 ou 14 dígitos)
- NUNCA tente gerar fatura sem CPF/CNPJ válido
"""
            
            # Fazer chamada inicial COM ferramentas disponíveis
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
                # Processar todas as ferramentas chamadas pela IA
                for tool_call in response.choices[0].message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"IA chamou função: {function_name} com argumentos: {function_args}")
                    
                    # Executar a função chamada pela IA
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
            if conversation:
                # Verificar capacidade de transferência do provedor ANTES de analisar
                provedor_capability = transfer_service.check_provedor_transfer_capability(provedor)
                logger.info(f"Capacidade de transferência do provedor {provedor.nome}: {provedor_capability.get('capability_score', 0)}%")
                
                # Analisar contexto da conversa para decidir transferência
                transfer_decision = transfer_service.analyze_transfer_decision(
                    mensagem=mensagem,
                    provedor=provedor,
                    conversation_context=conversation_memory.get('context', {}) if conversation_memory else {}
                )
                
                if transfer_decision:
                    logger.info(f"Decisão de transferência: {transfer_decision}")
                    
                    # Verificar se o provedor pode atender este tipo de transferência
                    transfer_type = transfer_decision.get('transfer_type')
                    if transfer_type and provedor_capability.get('can_handle_transfers', {}).get(transfer_type, {}).get('available', False):
                        # Marcar transferência na memória (versão síncrona)
                        redis_memory_service.set_conversation_memory_sync(
                            provedor_id=provedor.id,
                            conversation_id=conversation.id,
                            data={
                                'last_transfer': transfer_decision,
                                'transfer_executed_at': datetime.now().isoformat(),
                                'context:transfer_decision': transfer_decision
                            }
                        )
                        
                        logger.info(f"Transferência marcada para equipe: {transfer_decision['team_name']}")
                        
                        # Adicionar instrução de transferência ao prompt
                        system_prompt += f"""

IMPORTANTE - TRANSFERÊNCIA PARA EQUIPE ESPECIALIZADA:
- Baseado na conversa, transfira para: {transfer_decision['team_name']}
- Motivo: {transfer_decision['reason']}
- Confiança da detecção: {transfer_decision['confidence']:.1%}
- Informe ao cliente que será transferido para a equipe especializada
- Seja educado e explique o motivo da transferência
- Exemplo: "Vou transferir você para nossa equipe de {transfer_decision['team_name']} que é especializada em {transfer_decision['reason']}."
"""
                    else:
                        # O provedor não tem equipe para este tipo de transferência
                        logger.warning(f"Provedor {provedor.nome} não possui equipe para atender transferência do tipo: {transfer_type}")
                        
                        # Adicionar instrução para lidar com situação sem equipe adequada
                        system_prompt += f"""

IMPORTANTE - EQUIPE NÃO DISPONÍVEL:
- O cliente solicitou: {transfer_decision.get('reason', 'atendimento especializado')}
- INFELIZMENTE, não possuímos equipe especializada para este tipo de atendimento
- Tente resolver a solicitação do cliente da melhor forma possível
- Se não conseguir resolver, explique educadamente que não temos equipe especializada
- Ofereça alternativas ou encaminhe para atendimento geral
- NUNCA mencione equipes de outros provedores
- Exemplo: "Infelizmente não temos equipe especializada para {transfer_decision.get('reason', 'este tipo de atendimento')}, mas vou tentar te ajudar da melhor forma possível."
"""
                        
                        # Marcar na memória que não há equipe disponível
                        redis_memory_service.set_conversation_memory_sync(
                            provedor_id=provedor.id,
                            conversation_id=conversation.id,
                            data={
                                'transfer_attempted': True,
                                'transfer_type': transfer_type,
                                'no_team_available': True,
                                'reason': transfer_decision.get('reason'),
                                'timestamp': datetime.now().isoformat()
                            }
                        )
                else:
                    logger.info("Nenhuma transferência necessária para esta mensagem")
            
            # Verificar se precisa marcar que perguntou sobre ser cliente
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

openai_service = OpenAIService() 
