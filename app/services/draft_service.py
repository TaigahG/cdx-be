# services/draft_service.py

import json
from redis_client import get_redis
from typing import Optional, Dict

# Drafts expire after 24 hours
DRAFT_TTL_SECONDS = 24 * 60 * 60  # 86400 seconds


class DraftService:
    @staticmethod
    def _build_key(company_id: str, user_id: str, shipment_id: str, document_type: str) -> str:
        if hasattr(document_type, 'value'):
            document_type = document_type.value
        return f"draft:{company_id}:{user_id}:{shipment_id}:{document_type}"
    
    @staticmethod
    def _build_prefix(company_id: str, user_id: str, shipment_id: str) -> str:
        return f"draft:{company_id}:{user_id}:{shipment_id}:*"
    
    @staticmethod
    def save_draft(
        company_id: str,
        user_id: str,
        shipment_id: str,
        document_type: str,
        form_data: dict,
    ) -> dict:
        
        r = get_redis()
        key = DraftService._build_key(company_id, user_id, shipment_id, document_type)
        
        draft_data = {
            "company_id": company_id,
            "user_id": user_id,
            "shipment_id": shipment_id,
            "document_type": document_type.value if hasattr(document_type, 'value') else document_type,
            "form_data": form_data,
        }
        
        r.setex(key, DRAFT_TTL_SECONDS, json.dumps(draft_data))
        
        return {
            "success": True,
            "message": f"Draft saved for {document_type}",
            "expires_in": DRAFT_TTL_SECONDS,
        }
    
    @staticmethod
    def get_draft(
        company_id: str,
        user_id: str,
        shipment_id: str,
        document_type: str,
    ) -> Optional[dict]:
        
        r = get_redis()
        key = DraftService._build_key(company_id, user_id, shipment_id, document_type)
        
        data = r.get(key)
        if not data:
            return None
        
        draft = json.loads(data)
        
        ttl = r.ttl(key)
        draft["expires_in"] = ttl
        
        return draft
    
    @staticmethod
    def get_shipment_drafts(
        company_id: str,
        user_id: str,
        shipment_id: str,
    ) -> dict:
        """
        Get all drafts for a specific shipment.
        Returns a dict keyed by document_type.
        """
        r = get_redis()
        pattern = DraftService._build_prefix(company_id, user_id, shipment_id)
        
        drafts = {}
        for key in r.scan_iter(match=pattern):
            data = r.get(key)
            if data:
                draft = json.loads(data)
                doc_type = draft.get("document_type", "unknown")
                draft["expires_in"] = r.ttl(key)
                drafts[doc_type] = draft
        
        return {
            "shipment_id": shipment_id,
            "drafts": drafts,
            "total": len(drafts),
        }
    
    @staticmethod
    def delete_draft(
        company_id: str,
        user_id: str,
        shipment_id: str,
        document_type: str,
    ) -> bool:
        """
        Delete a specific draft. Called after the document is finalized
        and saved to PostgreSQL.
        """
        r = get_redis()
        key = DraftService._build_key(company_id, user_id, shipment_id, document_type)
        return r.delete(key) > 0
    
    @staticmethod
    def delete_shipment_drafts(
        company_id: str,
        user_id: str,
        shipment_id: str,
    ) -> int:
        """
        Delete all drafts for a shipment.
        Called when a shipment is finalized or cancelled.
        """
        r = get_redis()
        pattern = DraftService._build_prefix(company_id, user_id, shipment_id)
        
        deleted = 0
        for key in r.scan_iter(match=pattern):
            r.delete(key)
            deleted += 1
        
        return deleted