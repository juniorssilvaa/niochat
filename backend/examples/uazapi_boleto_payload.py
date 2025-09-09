"""
Exemplo de Payload para Uazapi - Boleto com Botão Interativo

Este exemplo mostra como enviar um boleto bancário com botão para copiar linha digitável
usando o endpoint /send/menu da Uazapi/Evolution API.
"""

# Payload para enviar boleto com botão de copiar linha digitável
boleto_payload = {
    "number": "556392484773",  # Número do cliente
    "type": "button",
    "text": "Boleto Bancário em PDF\nClique no botão para copiar a linha digitável:",
    "choices": [
        "Copiar Linha Digitável|copy:34191.00008 00000.000000 00000.000000 5 94830000012345"
    ],
    "footerText": "Dados da fatura foram enviados pela IA"
}

# Payload alternativo com imagem do boleto
boleto_com_imagem_payload = {
    "number": "556392484773",
    "type": "button",
    "text": "Boleto Bancário em PDF\nClique no botão para copiar a linha digitável:",
    "imageButton": "https://seuservidor.com/boleto_77803.pdf",  # URL do PDF ou imagem
    "choices": [
        "Copiar Linha Digitável|copy:34191.00008 00000.000000 00000.000000 5 94830000012345"
    ],
    "footerText": "Dados da fatura foram enviados pela IA"
}

# Payload para múltiplos botões (boleto + PIX)
boleto_pix_payload = {
    "number": "556392484773",
    "type": "button",
    "text": "Escolha a forma de pagamento:",
    "choices": [
        "Copiar Linha Digitável|copy:34191.00008 00000.000000 00000.000000 5 94830000012345",
        "Ver QR Code PIX|https://seuservidor.com/qr_pix_77803.png",
        "Baixar Boleto PDF|https://seuservidor.com/boleto_77803.pdf"
    ],
    "footerText": "Dados da fatura foram enviados pela IA"
}

# Payload para lista de faturas
lista_faturas_payload = {
    "number": "556392484773",
    "type": "list",
    "text": "Suas faturas pendentes:",
    "listButton": "Ver Faturas",
    "choices": [
        "[Faturas Vencidas]",
        "Fatura #77803|fatura_77803|Vencimento: 10/08/2025 - R$ 207,60",
        "Fatura #77804|fatura_77804|Vencimento: 15/08/2025 - R$ 189,90",
        "[Faturas a Vencer]",
        "Fatura #77805|fatura_77805|Vencimento: 25/08/2025 - R$ 207,60"
    ],
    "footerText": "Escolha uma fatura para gerar o boleto"
}

# Payload para enquete de satisfação
csat_payload = {
    "number": "556392484773",
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

# Função para enviar via Uazapi
def enviar_boleto_uazapi(provedor_config, numero_cliente, dados_boleto):
    """
    Envia boleto com botão interativo via Uazapi
    
    Args:
        provedor_config: Configuração do provedor (URL, token, instance)
        numero_cliente: Número do cliente
        dados_boleto: Dicionário com dados do boleto
    """
    
    payload = {
        "number": numero_cliente,
        "type": "button",
        "text": f"Boleto Bancário em PDF\nClique no botão para copiar a linha digitável:",
        "choices": [
            f"Copiar Linha Digitável|copy:{dados_boleto['linha_digitavel']}"
        ],
        "footerText": "Dados da fatura foram enviados pela IA"
    }
    
    # Se tiver URL do boleto, adicionar como imagem
    if dados_boleto.get('url_boleto'):
        payload["imageButton"] = dados_boleto['url_boleto']
    
    # URL da API Uazapi
    url = f"{provedor_config['api_url']}/send/menu/{provedor_config['instance']}"
    
    headers = {
        "Authorization": f"Bearer {provedor_config['token']}",
        "Content-Type": "application/json"
    }
    
    return {
        "url": url,
        "headers": headers,
        "payload": payload
    }

# Exemplo de uso
if __name__ == "__main__":
    # Configuração do provedor
    provedor_config = {
        "api_url": "http://192.168.100.55:8080",
        "instance": "giga_bom",
        "token": "seu_token_aqui"
    }
    
    # Dados do boleto
    dados_boleto = {
        "linha_digitavel": "34191.00008 00000.000000 00000.000000 5 94830000012345",
        "url_boleto": "https://seuservidor.com/boleto_77803.pdf",
        "valor": "R$ 207,60",
        "vencimento": "10/08/2025"
    }
    
    # Gerar payload
    resultado = enviar_boleto_uazapi(provedor_config, "556392484773", dados_boleto)
    
    print("URL:", resultado["url"])
    print("Headers:", resultado["headers"])
    print("Payload:", resultado["payload"])


