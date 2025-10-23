import pdfplumber
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Processador de PDFs para extrair informações de comprovantes de pagamento"""
    
    def __init__(self):
        self.payment_keywords = [
            'comprovante', 'pagamento', 'pix', 'transferência', 'depósito',
            'boleto', 'cartão', 'débito', 'crédito', 'valor', 'total',
            'recebido', 'pago', 'transação', 'operação'
        ]
        
        self.bank_keywords = [
            'banco', 'itau', 'bradesco', 'caixa', 'santander', 'nubank',
            'inter', 'sicoob', 'sicredi', 'banco do brasil', 'bb'
        ]
    
    def is_payment_receipt(self, text: str) -> bool:
        """Verifica se o PDF é um comprovante de pagamento"""
        text_lower = text.lower()
        
        # Contar palavras-chave de pagamento
        payment_count = sum(1 for keyword in self.payment_keywords if keyword in text_lower)
        bank_count = sum(1 for keyword in self.bank_keywords if keyword in text_lower)
        
        # Se tem pelo menos 2 palavras de pagamento e 1 de banco, provavelmente é comprovante
        return payment_count >= 2 and bank_count >= 1
    
    def extract_payment_info(self, pdf_path: str) -> Dict:
        """Extrai informações de comprovante de pagamento do PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                pages_info = []
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    full_text += f"\n--- Página {page_num} ---\n{page_text}"
                    
                    # Extrair tabelas se existirem
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = "\n".join([" | ".join(row) for row in table])
                            full_text += f"\n--- Tabela Página {page_num} ---\n{table_text}"
                    
                    pages_info.append({
                        'page': page_num,
                        'text': page_text,
                        'tables': tables or []
                    })
                
                # Verificar se é comprovante de pagamento
                if not self.is_payment_receipt(full_text):
                    return {
                        'is_payment_receipt': False,
                        'message': 'PDF não parece ser um comprovante de pagamento'
                    }
                
                # Extrair informações específicas
                payment_info = self._extract_payment_details(full_text)
                
                return {
                    'is_payment_receipt': True,
                    'full_text': full_text,
                    'pages_info': pages_info,
                    'payment_info': payment_info,
                    'extraction_date': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erro ao processar PDF {pdf_path}: {str(e)}")
            return {
                'is_payment_receipt': False,
                'error': str(e),
                'message': 'Erro ao processar o PDF'
            }
    
    def _extract_payment_details(self, text: str) -> Dict:
        """Extrai detalhes específicos do comprovante de pagamento"""
        details = {}
        
        # Extrair valores monetários
        money_patterns = [
            r'R\$\s*([\d.,]+)',
            r'valor[:\s]*R\$\s*([\d.,]+)',
            r'total[:\s]*R\$\s*([\d.,]+)',
            r'([\d.,]+)\s*reais?',
            r'R\$\s*([\d.,]+)'
        ]
        
        amounts = []
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Limpar e converter valor
                clean_amount = match.replace(',', '.').replace(' ', '')
                try:
                    amount = float(clean_amount)
                    if amount > 0:
                        amounts.append(amount)
                except ValueError:
                    continue
        
        if amounts:
            details['amount'] = max(amounts)  # Pegar o maior valor encontrado
            details['all_amounts'] = amounts
        
        # Extrair datas
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 3:
                        day, month, year = match
                        if int(month) <= 12 and int(day) <= 31:
                            dates.append(f"{day.zfill(2)}/{month.zfill(2)}/{year}")
                except ValueError:
                    continue
        
        if dates:
            details['dates'] = dates
        
        # Extrair informações do banco
        bank_info = self._extract_bank_info(text)
        if bank_info:
            details['bank_info'] = bank_info
        
        # Extrair tipo de transação
        transaction_type = self._extract_transaction_type(text)
        if transaction_type:
            details['transaction_type'] = transaction_type
        
        # Extrair número da transação/operação
        operation_patterns = [
            r'operação[:\s]*(\d+)',
            r'transação[:\s]*(\d+)',
            r'protocolo[:\s]*(\d+)',
            r'id[:\s]*(\d+)',
            r'número[:\s]*(\d+)'
        ]
        
        operations = []
        for pattern in operation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            operations.extend(matches)
        
        if operations:
            details['operation_numbers'] = operations
        
        # Extrair informações do beneficiário/remetente
        beneficiary_info = self._extract_beneficiary_info(text)
        if beneficiary_info:
            details['beneficiary'] = beneficiary_info
        
        return details
    
    def _extract_bank_info(self, text: str) -> Dict:
        """Extrai informações do banco"""
        bank_info = {}
        
        # Nome do banco
        for bank in self.bank_keywords:
            if bank in text.lower():
                bank_info['bank_name'] = bank.title()
                break
        
        # Agência e conta
        agency_pattern = r'agência[:\s]*(\d+)'
        account_pattern = r'conta[:\s]*(\d+)'
        
        agency_match = re.search(agency_pattern, text, re.IGNORECASE)
        account_match = re.search(account_pattern, text, re.IGNORECASE)
        
        if agency_match:
            bank_info['agency'] = agency_match.group(1)
        if account_match:
            bank_info['account'] = account_match.group(1)
        
        return bank_info
    
    def _extract_transaction_type(self, text: str) -> str:
        """Extrai o tipo de transação"""
        text_lower = text.lower()
        
        if 'pix' in text_lower:
            return 'PIX'
        elif 'transferência' in text_lower or 'transferencia' in text_lower:
            return 'Transferência'
        elif 'depósito' in text_lower or 'deposito' in text_lower:
            return 'Depósito'
        elif 'boleto' in text_lower:
            return 'Boleto'
        elif 'cartão' in text_lower or 'cartao' in text_lower:
            return 'Cartão'
        elif 'débito' in text_lower or 'debito' in text_lower:
            return 'Débito'
        elif 'crédito' in text_lower or 'credito' in text_lower:
            return 'Crédito'
        
        return 'Pagamento'
    
    def _extract_beneficiary_info(self, text: str) -> Dict:
        """Extrai informações do beneficiário"""
        beneficiary_info = {}
        
        # Nome do beneficiário
        name_patterns = [
            r'para[:\s]*([A-Za-z\s]+)',
            r'beneficiário[:\s]*([A-Za-z\s]+)',
            r'recebedor[:\s]*([A-Za-z\s]+)',
            r'favor[:\s]*([A-Za-z\s]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:  # Nome deve ter pelo menos 3 caracteres
                    beneficiary_info['name'] = name
                    break
        
        # CPF/CNPJ
        cpf_pattern = r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})'
        cnpj_pattern = r'(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})'
        
        cpf_match = re.search(cpf_pattern, text)
        cnpj_match = re.search(cnpj_pattern, text)
        
        if cpf_match:
            beneficiary_info['cpf'] = cpf_match.group(1)
        if cnpj_match:
            beneficiary_info['cnpj'] = cnpj_match.group(1)
        
        return beneficiary_info
    
    def generate_ai_prompt(self, payment_info: Dict) -> str:
        """Gera prompt estruturado com os dados extraídos do PDF para a IA principal processar"""
        if not payment_info.get('is_payment_receipt'):
            return "Este PDF não parece ser um comprovante de pagamento válido."
        
        details = payment_info.get('payment_info', {})
        
        # Gerar um prompt estruturado com os dados extraídos
        prompt_parts = []
        
        if details.get('amount'):
            prompt_parts.append(f"Valor: R$ {details['amount']:.2f}")
        
        if details.get('transaction_type'):
            prompt_parts.append(f"Tipo: {details['transaction_type']}")
        
        if details.get('dates'):
            prompt_parts.append(f"Data: {details['dates'][0]}")
        
        if details.get('beneficiary'):
            beneficiary = details['beneficiary']
            if beneficiary.get('name'):
                prompt_parts.append(f"Beneficiário: {beneficiary['name']}")
        
        if prompt_parts:
            prompt = f"""Dados extraídos do comprovante de pagamento:

{chr(10).join(prompt_parts)}

Com base nestes dados extraídos do PDF, responda ao cliente de forma contextualizada sobre o pagamento recebido."""
        else:
            prompt = "Comprovante de pagamento recebido, mas não foi possível extrair informações detalhadas."
        
        return prompt

# Instância global do processador
pdf_processor = PDFProcessor()
