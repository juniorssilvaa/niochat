import requests

class SGPClient:
    def __init__(self, base_url, token, app_name):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.app_name = app_name

    def _headers(self, include_content_type=True):
        headers = {
            'Authorization': f'Token {self.token}',
            'App': self.app_name
        }
        if include_content_type:
            headers['Content-Type'] = 'application/json'
        return headers

    def listar_clientes(self):
        return requests.get(f'{self.base_url}/api/ura/clientes/', headers=self._headers()).json()

    def consultar_cliente(self, cpf):
        params = {
            'token': self.token,
            'app': self.app_name,
            'cpfcnpj': cpf
        }
        return requests.get(f'{self.base_url}/api/ura/consultacliente/', params=params, headers=self._headers()).json()

    def verifica_acesso(self, contrato):
        data = {
            'token': self.token,
            'app': self.app_name,
            'contrato': contrato
        }
        # Não enviar Content-Type para form-data!
        return requests.post(f'{self.base_url}/api/ura/verificaacesso/', data=data, headers=self._headers(include_content_type=False)).json()

    def listar_contratos(self, cliente_id):
        return requests.post(f'{self.base_url}/api/ura/listacontrato/', json={'cliente_id': cliente_id}, headers=self._headers()).json()

    def liberar_por_confianca(self, contrato):
        return requests.post(f'{self.base_url}/api/ura/liberacaopromessa/', json={'contrato': contrato}, headers=self._headers()).json()

    def criar_chamado(self, contrato, ocorrenciatipo, conteudo):
        """
        Criar chamado técnico no SGP
        Args:
            contrato: ID do contrato
            ocorrenciatipo: Código do tipo de ocorrência (padrão: 1 para técnico)
            conteudo: Conteúdo principal do chamado (vai no campo "conteudo")
        """
        data = {
            'token': self.token,
            'app': self.app_name,
            'contrato': contrato,
            'ocorrenciatipo': ocorrenciatipo,
            'conteudo': conteudo
        }
            
        # Não enviar Content-Type para form-data!
        return requests.post(f'{self.base_url}/api/ura/chamado/', data=data, headers=self._headers(include_content_type=False)).json()

    def segunda_via_fatura(self, identificador):
        """
        Buscar segunda via da fatura usando CPF/CNPJ ou ID do contrato
        Args:
            identificador: CPF/CNPJ do cliente ou ID do contrato
        """
        # Enviar token apenas nos parâmetros (sem Content-Type para form-data)
        data = {
            'token': self.token,
            'app': self.app_name,
        }
        
        # Se é um número (contrato), usar campo 'contrato', senão usar 'cpfcnpj'
        if str(identificador).isdigit():
            data['contrato'] = identificador
        else:
            data['cpfcnpj'] = identificador
            
        # Não enviar Content-Type para form-data!
        return requests.post(f'{self.base_url}/api/ura/fatura2via/', data=data, headers=self._headers(include_content_type=False)).json()

    def gerar_pix(self, fatura):
        return requests.get(f'{self.base_url}/api/ura/pagamento/pix/{fatura}', headers=self._headers()).json()

    def listar_manutencoes(self, cpf):
        return requests.post(f'{self.base_url}/api/ura/manutencao/list/', json={'cpf': cpf}, headers=self._headers()).json() 