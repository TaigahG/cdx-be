from sqlalchemy.orm import Session
from crud import file_crud, company_crud, user_crud, shipment_crud
from crud.shipment_crud import get_shipment
from models import Folder, File
from schemas import FileCreate, FileUpdate
from typing import List, Optional

class FileService:
    """Business logic for files/documents"""
    
    @staticmethod
    def get_file(db: Session, file_id: int) -> Optional[File]:
        """Get file by ID"""
        return file_crud.get_file(db, file_id)
    
    @staticmethod
    def list_files(
        db: Session,
        company_id: str = None,
        shipment_id: str = None,
        folder_id: int = None,
        document_type: str = None,
        is_verified: bool = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """List all files"""
        return file_crud.get_files(
            db, company_id, shipment_id, folder_id, 
            document_type, is_verified, skip, limit
        )
    
    @staticmethod
    def create_file(db: Session, file: FileCreate) -> File:
        """Create file with validation"""  
        if not company_crud.company_exists(db, file.company_id):
            raise ValueError(f"Company with ID {file.company_id} not found")
        
        if not user_crud.get_user(db, file.user_id):
            raise ValueError(f"User with ID {file.user_id} not found")
        
        if file.shipment_id:
            shipment = get_shipment(db, file.shipment_id)
            if not shipment:
                raise ValueError(f"Shipment with ID {file.shipment_id} not found")
            
            shipment.document_count += 1
            db.commit()
        
        if file.folder_id:
            folder = db.query(Folder).filter(Folder.folder_id == file.folder_id).first()
            if not folder:
                raise ValueError(f"Folder with ID {file.folder_id} not found")
        
        return file_crud.create_file(db, file.model_dump(), document_type=file.document_type)
    
    @staticmethod
    def update_file(db: Session, file_id: int, file_update: FileUpdate) -> Optional[File]:
        """Update file with validation"""
        
        # Check file exists
        if not file_crud.get_file(db, file_id):
            raise ValueError(f"File with ID {file_id} not found")
        
        # Update file
        update_data = file_update.model_dump(exclude_unset=True)
        return file_crud.update_file(db, file_id, update_data)
    
    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        """Delete file with validation"""
        
        db_file = file_crud.get_file(db, file_id)
        if not db_file:
            raise ValueError(f"File with ID {file_id} not found")
        
        if db_file.shipment_id:
            shipment = get_shipment(db, db_file.shipment_id)
            if shipment and shipment.document_count > 0:
                shipment.document_count -= 1
                db.commit()
        
        return file_crud.delete_file(db, file_id)
    
    @staticmethod
    def verify_file(db: Session, file_id: int, is_verified: bool):
        """Update file verification status"""
        
        if not file_crud.get_file(db, file_id):
            raise ValueError(f"File with ID {file_id} not found")
        
        from datetime import datetime
        if is_verified:
            return file_crud.update_file(db, file_id, {'is_verified': True, 'verified_at': datetime.utcnow()})
        else:
            return file_crud.update_file(db, file_id, {'is_verified': False})
    
    @staticmethod
    def get_file_verification_history(db: Session, file_id: int):
        """Get file verification history"""
        
        db_file = file_crud.get_file(db, file_id)
        if not db_file:
            raise ValueError(f"File with ID {file_id} not found")
        
        verifications = file_crud.get_file_verifications(db, file_id)
        
        return {
            "file_id": file_id,
            "is_verified": db_file.is_verified,
            "verified_at": db_file.verified_at,
            "verification_history": verifications
        }

    @staticmethod
    def increment_verified(db: Session, document_type: str):
        """Increment verified counter for a document type"""
        file_crud.increment_doc_counter(db, document_type, "total_doc_verified")

    @staticmethod
    def increment_transferred(db: Session, document_type: str):
        """Increment transferred counter for a document type"""
        file_crud.increment_doc_counter(db, document_type, "total_doc_transferred")

    @staticmethod
    def get_analytics(db: Session):
        """Get document analytics for admin dashboard"""
        counters = file_crud.get_doc_counters(db)
        totals = file_crud.get_doc_counter_totals(db)
        return {
            "by_document_type": [
                {
                    "document_type": c.document_type,
                    "total_doc_created": c.total_doc_created,
                    "total_doc_verified": c.total_doc_verified,
                    "total_doc_transferred": c.total_doc_transferred
                } for c in counters
            ],
            "totals": totals
        }