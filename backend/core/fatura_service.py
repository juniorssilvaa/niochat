"""
Serviço para buscar faturas via endpoint SGP e enviar via Uazapi
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
from django.utils import timezone

logger = logging.getLogger(__name__)

class FaturaService:
    """Serviço para gerenciar faturas via SGP e Uazapi"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'NioChat/1.0'
        })

    def _formatar_cpf_cnpj(self, cpf_cnpj: str) -> str:
        """
        Formata CPF/CNPJ adicionando pontos e traços
        Args:
            cpf_cnpj: CPF ou CNPJ sem formatação
        Returns:
            CPF/CNPJ formatado
        """
        # Remover todos os caracteres não numéricos
        numeros = ''.join(filter(str.isdigit, cpf_cnpj))
        
        # Se já está formatado, retornar como está
        if '.' in cpf_cnpj or '-' in cpf_cnpj:
            return cpf_cnpj
        
        # Formatar CPF (11 dígitos)
        if len(numeros) == 11:
            return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
        
        # Formatar CNPJ (14 dígitos)
        elif len(numeros) == 14:
            return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
        
        # Se não for CPF nem CNPJ válido, retornar como está
        return cpf_cnpj

    def buscar_fatura_sgp(self, provedor, cpf_cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Busca fatura no SGP via endpoint /api/ura/fatura2via/ usando CPF/CNPJ diretamente
        
        Args:
            provedor: Objeto Provedor com configurações SGP
            cpf_cnpj: CPF ou CNPJ do cliente para buscar fatura
            
        Returns:
            Dados da fatura ou None se erro
        """
        try:
            # Importar SGPClient para usar a mesma autenticação
            from .sgp_client import SGPClient
            
            # Obter configurações do SGP do provedor (dinâmicas por provedor)
            integracao = provedor.integracoes_externas or {}
            sgp_url = integracao.get('sgp_url')
            sgp_token = integracao.get('sgp_token')
            sgp_app = integracao.get('sgp_app')
            
            if not all([sgp_url, sgp_token, sgp_app]):
                logger.error("Configurações do SGP não encontradas no provedor")
                return None
            
            # Criar cliente SGP com as configurações dinâmicas do provedor
            sgp = SGPClient(
                base_url=sgp_url,
                token=sgp_token,
                app_name=sgp_app
            )
            
            logger.info(f"Buscando fatura no SGP via SGPClient para CPF/CNPJ: {cpf_cnpj}")
            
            # Formatar CPF/CNPJ se necessário (adicionar pontos e traços)
            cpf_cnpj_formatado = self._formatar_cpf_cnpj(cpf_cnpj)
            logger.info(f"CPF/CNPJ formatado: {cpf_cnpj_formatado}")
            
            # Usar diretamente o CPF/CNPJ no método segunda_via_fatura
            resultado = sgp.segunda_via_fatura(cpf_cnpj_formatado)
            
            if resultado and resultado.get('status') == 1:
                logger.info(f"Fatura encontrada para CPF/CNPJ: {cpf_cnpj}")
                return resultado
            else:
                logger.warning(f"Fatura não encontrada para CPF/CNPJ: {cpf_cnpj}: {resultado.get('msg', 'Sem mensagem')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar fatura via SGPClient: {e}")
            return None

    def enviar_fatura_uazapi(self, provedor, numero_whatsapp: str, dados_fatura: Dict[str, Any], conversation=None, tipo_pagamento: str = 'pix') -> bool:
        """
        Envia fatura completa via Uazapi: mensagem + QR code (PIX) ou PDF (Boleto) + botões apropriados
        E salva todas as mensagens no banco do Nio Chat
        
        Args:
            provedor: Objeto Provedor com configurações
            numero_whatsapp: Número do WhatsApp do cliente
            dados_fatura: Dados da fatura do SGP
            conversation: Objeto Conversation para salvar mensagens no banco
            tipo_pagamento: 'pix' ou 'boleto' - define quais botões enviar
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            from .uazapi_client import UazapiClient
            from .qr_code_service import qr_code_service
            
            # Obter configurações do Uazapi do provedor (campos corretos)
            integracao = provedor.integracoes_externas or {}
            uazapi_url = integracao.get('whatsapp_url')  # Corrigido: whatsapp_url
            uazapi_token = integracao.get('whatsapp_token')  # Corrigido: whatsapp_token
            
            if not all([uazapi_url, uazapi_token]):
                logger.error(f"Configurações do Uazapi não encontradas. whatsapp_url: {uazapi_url}, whatsapp_token: {'Configurado' if uazapi_token else 'Não configurado'}")
                return False
            
            # Criar cliente Uazapi
            uazapi = UazapiClient(base_url=uazapi_url, token=uazapi_token)
            
            if not dados_fatura.get('links'):
                logger.error("Dados da fatura não contêm links de pagamento")
                return False
            
            # Pegar primeira fatura
            fatura = dados_fatura['links'][0]
            codigo_pix = fatura.get('codigopix')
            linha_digitavel = fatura.get('linhadigitavel')
            link_fatura = fatura.get('link')
            
            # 1. ENVIAR MENSAGEM ANTIGA DA FATURA (COMO NAS IMAGENS)
            fatura = dados_fatura.get('links', [{}])[0]
            fatura_id = fatura.get('fatura', 'N/A')
            vencimento = fatura.get('vencimento_original') or fatura.get('vencimento', 'N/A')
            valor = fatura.get('valor', 0)
            
            # Formatar vencimento para dd/mm/yyyy
            vencimento_formatado = vencimento
            if vencimento and '-' in str(vencimento):
                try:
                    vencimento_date = datetime.strptime(vencimento, "%Y-%m-%d")
                    vencimento_formatado = vencimento_date.strftime("%d/%m/%Y")
                except:
                    pass
            
            # Formatar valor
            valor_formatado = f"R$ {valor:.2f}".replace('.', ',') if valor else "R$ 0,00"
            
            # Determinar se está vencida
            status_vencimento = "está vencida" if vencimento else "está em aberto"
            if vencimento:
                try:
                    vencimento_date = datetime.strptime(vencimento, "%Y-%m-%d")
                    hoje = datetime.now()
                    if vencimento_date < hoje:
                        status_vencimento = "está vencida"
                    else:
                        status_vencimento = "está em aberto"
                except:
                    status_vencimento = "está em aberto"
            
            mensagem_fatura = f"💳 Sua fatura {status_vencimento}:\n\nFatura ID: {fatura_id}\nVencimento: {vencimento_formatado}\nValor: {valor_formatado}"
            
            resultado_mensagem = uazapi.enviar_mensagem(numero_whatsapp, mensagem_fatura)
            
            if not resultado_mensagem:
                logger.error("Falha ao enviar mensagem da fatura")
                return False
            
            # SALVAR MENSAGEM DA FATURA NO BANCO
            if conversation:
                try:
                    from conversations.models import Message
                    Message.objects.create(
                        conversation=conversation,
                        message_type='text',
                        content=mensagem_fatura,
                        is_from_customer=False,
                        created_at=timezone.now()
                    )
                    logger.info("✅ Mensagem da fatura salva no banco")
                except Exception as e:
                    logger.warning(f"Erro ao salvar mensagem da fatura no banco: {e}")
            
            # 2. ENVIAR QR CODE PIX (apenas para PIX) ou PDF BOLETO (apenas para Boleto)
            if tipo_pagamento == 'pix' and codigo_pix:
                # Gerar QR code PIX
                qr_code_bytes = qr_code_service.gerar_qr_code_pix_bytes(codigo_pix)
                
                if qr_code_bytes:
                    resultado_qr = uazapi.enviar_imagem(
                        numero=numero_whatsapp,
                        imagem_bytes=qr_code_bytes,
                        legenda="QR Code PIX para pagamento"
                    )
                    
                    if not resultado_qr:
                        logger.error("Falha ao enviar QR code PIX")
                        return {"success": False, "error": "Falha ao enviar QR code PIX"}
                    
                    # SALVAR MENSAGEM DO QR CODE NO BANCO
                    if conversation:
                        try:
                            from conversations.models import Message
                            # Salvar como mensagem de imagem
                            Message.objects.create(
                                conversation=conversation,
                                message_type='image',
                                content="QR Code PIX para pagamento",
                                is_from_customer=False,
                                file_url=f"/api/media/qr_code_pix_{conversation.id}.png",
                                created_at=timezone.now()
                            )
                            logger.info("✅ Mensagem do QR Code salva no banco")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem do QR Code no banco: {e}")
                else:
                    logger.warning("QR code PIX não pôde ser gerado")
                    return {"success": False, "error": "QR code PIX não pôde ser gerado"}
                    
            elif tipo_pagamento == 'boleto' and link_fatura:
                # Para Boleto: enviar PDF diretamente (sem mensagem extra)
                # Agora enviar o PDF do boleto diretamente via URL
                resultado_pdf = uazapi.enviar_documento(
                    numero=numero_whatsapp,
                    documento_url=link_fatura,
                    nome_arquivo=f"boleto_{fatura.get('fatura', 'N/A')}.pdf",
                    legenda="Boleto Bancário em PDF"
                )
                
                if resultado_pdf:
                    # SALVAR MENSAGEM DO PDF NO BANCO
                    if conversation:
                        try:
                            from conversations.models import Message
                            Message.objects.create(
                                conversation=conversation,
                                message_type='document',
                                content="📄 Boleto Bancário em PDF",
                                is_from_customer=False,
                                file_url=link_fatura,
                                created_at=timezone.now()
                            )
                            logger.info("✅ Mensagem do PDF do boleto salva no banco")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem do PDF no banco: {e}")
                    
                    logger.info("✅ PDF do boleto enviado com sucesso")
                else:
                    logger.error("Falha ao enviar PDF do boleto")
                    return {"success": False, "error": "Falha ao enviar PDF do boleto"}
            
            # 3. ENVIAR BOTÕES INTERATIVOS APROPRIADOS PARA O TIPO DE PAGAMENTO
            choices = []
            
            if tipo_pagamento == 'pix' and codigo_pix:
                # Para PIX: apenas botão "Copiar Chave PIX"
                # Tentar formato alternativo com \n em vez de |
                choices.append(f"Copiar Chave PIX\ncopy:{codigo_pix}")
                texto_botoes = "Clique para copiar a chave PIX:"
                footer_text = "Copie e cole o código no aplicativo do seu banco."
                
            elif tipo_pagamento == 'boleto' and linha_digitavel:
                # Para Boleto: apenas botão "Copiar Linha Digitável"
                choices.append(f"Copiar Linha Digitável|copy:{linha_digitavel}")
                texto_botoes = "Clique no botão para copiar a linha digitável:"
                footer_text = "Clique para copiar a linha digitável"
            
            # Enviar botões interativos se houver
            if choices:
                resultado_botoes = uazapi.enviar_menu(
                    numero=numero_whatsapp,
                    tipo="button",
                    texto=texto_botoes,
                    choices=choices,
                    footer_text=footer_text
                )
                
                if not resultado_botoes:
                    logger.error("Falha ao enviar botões interativos")
                    return {"success": False, "error": "Falha ao enviar botões interativos"}
                
                # SALVAR MENSAGEM DOS BOTÕES NO BANCO
                if conversation:
                    try:
                        from conversations.models import Message
                        # Salvar como mensagem com botões interativos
                        botao_texto = f"{texto_botoes}\n\n"
                        for choice in choices:
                            if "|" in choice:
                                nome, acao = choice.split("|", 1)
                                botao_texto += f"🔘 {nome}\n"
                        
                        botao_texto += f"\n{footer_text}"
                        
                        Message.objects.create(
                            conversation=conversation,
                            message_type='text',
                            content=botao_texto,
                            is_from_customer=False,
                            additional_attributes={
                                'has_buttons': True,
                                'button_choices': choices,
                                'is_interactive': True
                            },
                            created_at=timezone.now()
                        )
                        logger.info("✅ Mensagem dos botões interativos salva no banco")
                    except Exception as e:
                        logger.warning(f"Erro ao salvar mensagem dos botões no banco: {e}")
            
            logger.info(f"Fatura enviada com sucesso para {numero_whatsapp}")
            return {"success": True, "message": "Fatura enviada com sucesso"}
            
        except Exception as e:
            logger.error(f"Erro ao enviar fatura via Uazapi: {e}")
            return {"success": False, "error": str(e)}

    def enviar_formato_adicional(self, provedor, numero_whatsapp: str, dados_fatura: Dict[str, Any], formato_solicitado: str, conversation=None) -> bool:
        """
        Envia formato adicional de pagamento (PIX ou Boleto) quando cliente pede depois
        
        Args:
            provedor: Objeto Provedor com configurações
            numero_whatsapp: Número do WhatsApp do cliente
            dados_fatura: Dados da fatura do SGP
            formato_solicitado: 'pix' ou 'boleto' - o formato que o cliente pediu adicionalmente
            conversation: Objeto Conversation para salvar mensagens no banco
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            from .uazapi_client import UazapiClient
            from .qr_code_service import qr_code_service
            
            # Obter configurações do Uazapi
            integracao = provedor.integracoes_externas or {}
            uazapi_url = integracao.get('whatsapp_url')
            uazapi_token = integracao.get('whatsapp_token')
            
            if not all([uazapi_url, uazapi_token]):
                logger.error("Configurações do Uazapi não encontradas")
                return {"success": False, "error": "Configurações do Uazapi não encontradas"}
            
            # Criar cliente Uazapi
            uazapi = UazapiClient(base_url=uazapi_url, token=uazapi_token)
            
            if not dados_fatura.get('links'):
                logger.error("Dados da fatura não contêm links de pagamento")
                return {"success": False, "error": "Dados da fatura não contêm links de pagamento"}
            
            # Pegar primeira fatura
            fatura = dados_fatura['links'][0]
            
            if formato_solicitado.lower() == 'pix':
                # Enviar apenas PIX adicional
                codigo_pix = fatura.get('codigopix')
                
                if not codigo_pix:
                    logger.warning("Código PIX não disponível para esta fatura")
                    return {"success": False, "error": "Código PIX não disponível para esta fatura"}
                
                # 1. Enviar QR Code PIX
                qr_code_bytes = qr_code_service.gerar_qr_code_pix_bytes(codigo_pix)
                
                if qr_code_bytes:
                    resultado_qr = uazapi.enviar_imagem(
                        numero=numero_whatsapp,
                        imagem_bytes=qr_code_bytes,
                        legenda="QR Code PIX para pagamento"
                    )
                    
                    if resultado_qr:
                        # SALVAR MENSAGEM DO QR CODE NO BANCO
                        if conversation:
                            try:
                                from conversations.models import Message
                                Message.objects.create(
                                    conversation=conversation,
                                    message_type='image',
                                    content="QR Code PIX para pagamento",
                                    is_from_customer=False,
                                    file_url=f"/api/media/qr_code_pix_{conversation.id}.png",
                                    created_at=timezone.now()
                                )
                                logger.info("✅ Mensagem do QR Code adicional salva no banco")
                            except Exception as e:
                                logger.warning(f"Erro ao salvar mensagem do QR Code adicional no banco: {e}")
                    else:
                                            logger.error("Falha ao enviar QR code PIX adicional")
                    return {"success": False, "error": "Falha ao enviar QR code PIX adicional"}
                else:
                    logger.warning("QR code PIX não pôde ser gerado")
                    return {"success": False, "error": "QR code PIX não pôde ser gerado"}
                
                # 2. Enviar botão "Copiar Chave PIX"
                # Tentar formato alternativo com \n em vez de |
                choices = [f"Copiar Chave PIX\ncopy:{codigo_pix}"]
                texto_botoes = "Clique para copiar a chave PIX:"
                footer_text = "Copie e cole o código no aplicativo do seu banco."
                
                # Debug: verificar se o código PIX está completo
                logger.info(f"🔍 Código PIX completo: {codigo_pix}")
                logger.info(f"🔍 Tamanho do código PIX: {len(codigo_pix)} caracteres")
                logger.info(f"🔍 Choice do botão (formato \\n): {choices[0]}")
                
                resultado_botoes = uazapi.enviar_menu(
                    numero=numero_whatsapp,
                    tipo="button",
                    texto=texto_botoes,
                    choices=choices,
                    footer_text=footer_text
                )
                
                if resultado_botoes:
                    # SALVAR MENSAGEM DOS BOTÕES NO BANCO
                    if conversation:
                        try:
                            from conversations.models import Message
                            botao_texto = f"{texto_botoes}\n\n🔘 Copiar Chave PIX\n\n{footer_text}"
                            
                            Message.objects.create(
                                conversation=conversation,
                                message_type='text',
                                content=botao_texto,
                                is_from_customer=False,
                                additional_attributes={
                                    'has_buttons': True,
                                    'button_choices': choices,
                                    'is_interactive': True
                                },
                                created_at=timezone.now()
                            )
                            logger.info("✅ Mensagem dos botões PIX adicionais salva no banco")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem dos botões PIX adicionais no banco: {e}")
                    
                    logger.info("✅ PIX adicional enviado com sucesso")
                    return {"success": True, "message": "PIX adicional enviado com sucesso"}
                else:
                    logger.error("Falha ao enviar botões PIX adicionais")
                    return {"success": False, "error": "Falha ao enviar botões PIX adicionais"}
                    
            elif formato_solicitado.lower() == 'boleto':
                # Enviar apenas Boleto adicional
                linha_digitavel = fatura.get('linhadigitavel')
                link_boleto = fatura.get('link')
                
                if not linha_digitavel or not link_boleto:
                    logger.warning("Linha digitável ou link do boleto não disponível")
                    return {"success": False, "error": "Linha digitável ou link do boleto não disponível"}
                
                # 1. Enviar PDF do boleto
                resultado_pdf = uazapi.enviar_documento(
                    numero=numero_whatsapp,
                    documento_url=link_boleto,
                    nome_arquivo=f"boleto_{fatura.get('fatura', 'N/A')}.pdf",
                    legenda="Boleto Bancário em PDF"
                )
                
                if resultado_pdf:
                    # SALVAR MENSAGEM DO PDF NO BANCO
                    if conversation:
                        try:
                            from conversations.models import Message
                            Message.objects.create(
                                conversation=conversation,
                                message_type='document',
                                content="📄 Boleto Bancário em PDF",
                                is_from_customer=False,
                                file_url=link_boleto,
                                created_at=timezone.now()
                            )
                            logger.info("✅ Mensagem do PDF do boleto adicional salva no banco")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem do PDF adicional no banco: {e}")
                    
                    logger.info("✅ PDF do boleto adicional enviado com sucesso")
                else:
                    logger.error("Falha ao enviar PDF do boleto adicional")
                    return {"success": False, "error": "Falha ao enviar PDF do boleto adicional"}
                
                # 2. Enviar botão "Copiar Linha Digitável"
                choices = [f"Copiar Linha Digitável|copy:{linha_digitavel}"]
                texto_botoes = "Clique no botão para copiar a linha digitável:"
                footer_text = "Clique para copiar a linha digitável"
                
                resultado_botoes = uazapi.enviar_menu(
                    numero=numero_whatsapp,
                    tipo="button",
                    texto=texto_botoes,
                    choices=choices,
                    footer_text=footer_text
                )
                
                if resultado_botoes:
                    # SALVAR MENSAGEM DOS BOTÕES NO BANCO
                    if conversation:
                        try:
                            from conversations.models import Message
                            botao_texto = f"{texto_botoes}\n\n🔘 Copiar Linha Digitável\n\n{footer_text}"
                            
                            Message.objects.create(
                                conversation=conversation,
                                message_type='text',
                                content=botao_texto,
                                is_from_customer=False,
                                additional_attributes={
                                    'has_buttons': True,
                                    'button_choices': choices,
                                    'is_interactive': True
                                },
                                created_at=timezone.now()
                            )
                            logger.info("✅ Mensagem dos botões boleto adicionais salva no banco")
                        except Exception as e:
                            logger.warning(f"Erro ao salvar mensagem dos botões boleto adicionais no banco: {e}")
                    
                    logger.info("✅ Boleto adicional enviado com sucesso")
                    return {"success": True, "message": "Boleto adicional enviado com sucesso"}
                else:
                    logger.error("Falha ao enviar botões boleto adicionais")
                    return {"success": False, "error": "Falha ao enviar botões boleto adicionais"}
            else:
                logger.error(f"Formato solicitado inválido: {formato_solicitado}")
                return {"success": False, "error": f"Formato solicitado inválido: {formato_solicitado}"}
                
        except Exception as e:
            logger.error(f"Erro ao enviar formato adicional: {e}")
            return {"success": False, "error": str(e)}

# Instância global do serviço
fatura_service = FaturaService()
