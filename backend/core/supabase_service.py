import json
import logging
from typing import Any, Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Cliente simples para enviar Auditoria e CSAT ao Supabase via REST.

    Usa configurações do Django settings.py
    """

    def __init__(self) -> None:
        self.base_url: str = getattr(settings, 'SUPABASE_URL', '').rstrip("/")
        self.api_key: str = getattr(settings, 'SUPABASE_ANON_KEY', '')

        # Tabelas (ajuste os nomes conforme seu esquema no Supabase)
        self.audit_table: str = getattr(settings, 'SUPABASE_AUDIT_TABLE', 'auditoria')
        self.messages_table: str = getattr(settings, 'SUPABASE_MESSAGES_TABLE', 'mensagens')
        self.csat_table: str = getattr(settings, 'SUPABASE_CSAT_TABLE', 'csat_feedback')

        if not self.base_url or not self.api_key:
            logger.warning("Supabase não configurado (SUPABASE_URL/SUPABASE_ANON_KEY ausentes). Integração ficará desabilitada.")

    def _headers(self, provedor_id: int = None) -> Dict[str, str]:
        headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",  # não precisamos do payload de volta
        }
        
        # Adicionar provedor_id no header para RLS
        if provedor_id:
            headers["X-Provedor-ID"] = str(provedor_id)
            
        return headers

    def _is_enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _post(self, table: str, payload: Dict[str, Any], provedor_id: int = None) -> bool:
        if not self._is_enabled():
            return False
        try:
            url = f"{self.base_url}/rest/v1/{table}"
            response = requests.post(url, headers=self._headers(provedor_id), data=json.dumps(payload), timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            logger.warning(f"Falha ao enviar para Supabase ({table}): {response.status_code} - {response.text}")
            return False
        except Exception as exc:
            logger.error(f"Erro ao enviar dados ao Supabase ({table}): {exc}")
            return False

    def save_audit(self, *, provedor_id: int, conversation_id: int, action: str, details: Dict[str, Any],
                   user_id: Optional[int] = None, ended_at_iso: Optional[str] = None) -> bool:
        payload: Dict[str, Any] = {
            "provedor_id": provedor_id,
            "conversation_id": conversation_id,
            "action": action,
            "details": details,
        }
        if user_id is not None:
            payload["user_id"] = user_id
        if ended_at_iso is not None:
            payload["ended_at"] = ended_at_iso
        return self._post(self.audit_table, payload, provedor_id)

    def save_message(self, *, provedor_id: int, conversation_id: int, contact_id: int,
                     content: str, message_type: str = 'text', is_from_customer: bool = True,
                     external_id: Optional[str] = None, file_url: Optional[str] = None,
                     file_name: Optional[str] = None, file_size: Optional[int] = None,
                     additional_attributes: Optional[Dict[str, Any]] = None,
                     created_at_iso: Optional[str] = None) -> bool:
        payload: Dict[str, Any] = {
            "provedor_id": provedor_id,
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "content": content,
            "message_type": message_type,
            "is_from_customer": is_from_customer,
        }
        if external_id is not None:
            payload["external_id"] = external_id
        if file_url is not None:
            payload["file_url"] = file_url
        if file_name is not None:
            payload["file_name"] = file_name
        if file_size is not None:
            payload["file_size"] = file_size
        if additional_attributes is not None:
            payload["additional_attributes"] = additional_attributes
        if created_at_iso is not None:
            payload["created_at"] = created_at_iso
        return self._post(self.messages_table, payload, provedor_id)

    def save_csat(self, *, provedor_id: int, conversation_id: int, contact_id: int,
                  emoji_rating: str, rating_value: int, feedback_sent_at_iso: Optional[str] = None) -> bool:
        payload: Dict[str, Any] = {
            "provedor_id": provedor_id,
            "conversation_id": conversation_id,
            "contact_id": contact_id,
            "emoji_rating": emoji_rating,
            "rating_value": rating_value,
        }
        if feedback_sent_at_iso is not None:
            payload["feedback_sent_at"] = feedback_sent_at_iso
        return self._post(self.csat_table, payload, provedor_id)

    def save_conversation(self, *, provedor_id: int, conversation_id: int, contact_id: int,
                         inbox_id: Optional[int] = None, status: str = 'open',
                         assignee_id: Optional[int] = None, created_at_iso: Optional[str] = None,
                         updated_at_iso: Optional[str] = None, ended_at_iso: Optional[str] = None,
                         additional_attributes: Optional[Dict[str, Any]] = None) -> bool:
        payload: Dict[str, Any] = {
            "id": conversation_id,
            "provedor_id": provedor_id,
            "contact_id": contact_id,
            "status": status,
        }
        if inbox_id is not None:
            payload["inbox_id"] = inbox_id
        if assignee_id is not None:
            payload["assignee_id"] = assignee_id
        if created_at_iso is not None:
            payload["created_at"] = created_at_iso
        if updated_at_iso is not None:
            payload["updated_at"] = updated_at_iso
        if ended_at_iso is not None:
            payload["ended_at"] = ended_at_iso
        if additional_attributes is not None:
            payload["additional_attributes"] = additional_attributes
        return self._post("conversations", payload, provedor_id)

    def save_contact(self, *, provedor_id: int, contact_id: int, name: str,
                    phone: Optional[str] = None, email: Optional[str] = None,
                    avatar: Optional[str] = None, created_at_iso: Optional[str] = None,
                    updated_at_iso: Optional[str] = None, additional_attributes: Optional[Dict[str, Any]] = None) -> bool:
        payload: Dict[str, Any] = {
            "id": contact_id,
            "provedor_id": provedor_id,
            "name": name,
        }
        if phone is not None:
            payload["phone"] = phone
        if email is not None:
            payload["email"] = email
        if avatar is not None:
            payload["avatar"] = avatar
        if created_at_iso is not None:
            payload["created_at"] = created_at_iso
        if updated_at_iso is not None:
            payload["updated_at"] = updated_at_iso
        if additional_attributes is not None:
            payload["additional_attributes"] = additional_attributes
        return self._post("contacts", payload, provedor_id)


supabase_service = SupabaseService()


