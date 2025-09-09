"""
Integração Uazapi Menu - Sistema Nio Chat

Este módulo integra os botões interativos da Uazapi com o sistema existente,
sem quebrar funcionalidades já implementadas.
"""

import requests
import json
from typing import Dict, List, Optional

class UazapiMenuService:
    """
    Serviço para enviar mensagens interativas via Uazapi/Evolution API
    """
    
    def __init__(self, provedor_config: Dict):
        self.api_url = provedor_config.get('api_url')
        self.instance = provedor_config.get('instance')
        self.token = provedor_config.get('token')
    
    def enviar_boleto_interativo(self, numero_cliente: str, dados_boleto: Dict) -> Dict:
        """
        Envia boleto com botão para copiar linha digitável
        
        Args:
            numero_cliente: Número do cliente
            dados_boleto: Dados do boleto (linha_digitavel, url_boleto, etc.)
        
        Returns:
            Dict com resultado da operação
        """
        try:
            payload = {
                "number": numero_cliente,
                "type": "button",
                "text": "Boleto Bancário em PDF\nClique no botão para copiar a linha digitável:",
                "choices": [
                    f"Copiar Linha Digitável|copy:{dados_boleto['linha_digitavel']}"
                ],
                "footerText": "Dados da fatura foram enviados pela IA"
            }
            
            # Adicionar imagem se disponível
            if dados_boleto.get('url_boleto'):
                payload["imageButton"] = dados_boleto['url_boleto']
            
            return self._enviar_menu(payload)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar boleto interativo: {str(e)}"
            }
    
    def enviar_fatura_completa(self, numero_cliente: str, dados_fatura: Dict) -> Dict:
        """
        Envia fatura com múltiplos botões (boleto + PIX)
        
        Args:
            numero_cliente: Número do cliente
            dados_fatura: Dados da fatura
        
        Returns:
            Dict com resultado da operação
        """
        try:
            choices = []
            
            # Botão para copiar linha digitável
            if dados_fatura.get('linha_digitavel'):
                choices.append(f"Copiar Linha Digitável|copy:{dados_fatura['linha_digitavel']}")
            
            # Botão para QR Code PIX
            if dados_fatura.get('qr_code_pix'):
                choices.append(f"Ver QR Code PIX|{dados_fatura['qr_code_pix']}")
            
            # Botão para baixar boleto
            if dados_fatura.get('url_boleto'):
                choices.append(f"Baixar Boleto PDF|{dados_fatura['url_boleto']}")
            
            payload = {
                "number": numero_cliente,
                "type": "button",
                "text": "Escolha a forma de pagamento:",
                "choices": choices,
                "footerText": "Dados da fatura foram enviados pela IA"
            }
            
            return self._enviar_menu(payload)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar fatura completa: {str(e)}"
            }
    
    def enviar_lista_faturas(self, numero_cliente: str, faturas: List[Dict]) -> Dict:
        """
        Envia lista de faturas pendentes
        
        Args:
            numero_cliente: Número do cliente
            faturas: Lista de faturas
        
        Returns:
            Dict com resultado da operação
        """
        try:
            choices = ["[Faturas Pendentes]"]
            
            for fatura in faturas:
                descricao = f"Vencimento: {fatura['vencimento']} - {fatura['valor']}"
                choices.append(f"Fatura #{fatura['id']}|fatura_{fatura['id']}|{descricao}")
            
            payload = {
                "number": numero_cliente,
                "type": "list",
                "text": "Suas faturas pendentes:",
                "listButton": "Ver Faturas",
                "choices": choices,
                "footerText": "Escolha uma fatura para gerar o boleto"
            }
            
            return self._enviar_menu(payload)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar lista de faturas: {str(e)}"
            }
    
    def enviar_csat(self, numero_cliente: str) -> Dict:
        """
        Envia enquete de satisfação
        
        Args:
            numero_cliente: Número do cliente
        
        Returns:
            Dict com resultado da operação
        """
        try:
            payload = {
                "number": numero_cliente,
                "type": "poll",
                "text": "Como foi seu atendimento hoje?",
                "choices": [
                    "Péssimo",
                    "Ruim", 
                    "Regular",
                    "Bom",
                    "Excelente"
                ],
                "selectableCount": 1
            }
            
            return self._enviar_menu(payload)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar CSAT: {str(e)}"
            }
    
    def _enviar_menu(self, payload: Dict) -> Dict:
        """
        Envia menu interativo via Uazapi
        
        Args:
            payload: Payload da mensagem
        
        Returns:
            Dict com resultado da operação
        """
        try:
            url = f"{self.api_url}/send/menu/{self.instance}"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Menu enviado com sucesso"
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro na API: {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Erro de conexão: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro inesperado: {str(e)}"
            }

# Exemplo de integração com o sistema existente
def integrar_com_sistema_existente():
    """
    Exemplo de como integrar com o sistema existente sem quebrar funcionalidades
    """
    
    # Configuração do provedor (usar dados existentes)
    provedor_config = {
        "api_url": "http://192.168.100.55:8080",
        "instance": "giga_bom", 
        "token": "seu_token_aqui"
    }
    
    # Instanciar serviço
    uazapi_service = UazapiMenuService(provedor_config)
    
    # Exemplo 1: Enviar boleto simples
    dados_boleto = {
        "linha_digitavel": "34191.00008 00000.000000 00000.000000 5 94830000012345",
        "url_boleto": "https://seuservidor.com/boleto_77803.pdf"
    }
    
    resultado = uazapi_service.enviar_boleto_interativo("556392484773", dados_boleto)
    print("Resultado boleto:", resultado)
    
    # Exemplo 2: Enviar fatura completa
    dados_fatura = {
        "linha_digitavel": "34191.00008 00000.000000 00000.000000 5 94830000012345",
        "url_boleto": "https://seuservidor.com/boleto_77803.pdf",
        "qr_code_pix": "https://seuservidor.com/qr_pix_77803.png"
    }
    
    resultado = uazapi_service.enviar_fatura_completa("556392484773", dados_fatura)
    print("Resultado fatura completa:", resultado)
    
    # Exemplo 3: Enviar CSAT
    resultado = uazapi_service.enviar_csat("556392484773")
    print("Resultado CSAT:", resultado)

if __name__ == "__main__":
    integrar_com_sistema_existente()


