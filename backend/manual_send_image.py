#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'niochat.settings')
django.setup()

from core.models import Provedor
from core.uazapi_client import UazapiClient

TARGET_NUMBER = '556392484773'
INSTANCE_ID = None  # será descoberto pelo status

# Escolher provedor com whatsapp_instance configurado (GIGA BOM)
provedor = Provedor.objects.filter(integracoes_externas__whatsapp_instance__isnull=False).first()
if not provedor:
    print('❌ Nenhum provedor com whatsapp_instance configurado')
    raise SystemExit(1)

integracoes = provedor.integracoes_externas or {}
base_url = integracoes.get('whatsapp_url')
token = integracoes.get('whatsapp_token')

print(f'Provedor: {provedor.nome}')
print(f'Base URL: {base_url}')
print(f'Token set: {bool(token)}')

client = UazapiClient(base_url, token)

# Tentar obter instance_id via status do número
whats_instance = integracoes.get('whatsapp_instance')
print(f'whatsapp_instance: {whats_instance}')

# Descobrir instance_id via get_instance_status de canais conhecidos
# Aqui assumimos que existe pelo menos uma instância ativa no servidor desta URL
try:
    # Se o provedor armazenou algum instance_id nos canais, usar; caso contrário, confiar no número
    # Nota: Para o envio, a Uazapi geralmente não exige instance quando há somente uma ativa no token
    pass
except Exception:
    pass

# Selecionar uma imagem local salva recentemente (pegar a mais recente em media/messages)
media_root = os.path.join(os.path.dirname(__file__), 'media', 'messages')
chosen_file = None
for root, dirs, files in os.walk(media_root):
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if image_files:
        # pegar a primeira
        chosen_file = os.path.join(root, sorted(image_files)[-1])
        break

if not chosen_file:
    print('❌ Nenhum arquivo de imagem encontrado em media/messages')
    raise SystemExit(1)

print(f'Usando imagem: {chosen_file}')

with open(chosen_file, 'rb') as f:
    img_bytes = f.read()

ok = client.enviar_imagem(TARGET_NUMBER, img_bytes, legenda='', instance_id=INSTANCE_ID)
print('Resultado envio:', ok)


