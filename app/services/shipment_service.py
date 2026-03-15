from sqlalchemy.orm import Session
from crud import shipment_crud, company_crud, user_crud
from schemas import ShipmentCreate, ShipmentUpdate
from typing import List, Optional
from models import Shipment
from datetime import datetime
from utils import generate_shipment_id

class ShipmentService:
    """Business logic for shipments"""
    
    @staticmethod
    def get_shipment(db: Session, shipment_id: str) -> Optional[Shipment]:
        """Get shipment by ID"""
        return shipment_crud.get_shipment(db, shipment_id)
    
    @staticmethod
    def list_shipments(
        db: Session,
        company_id: str = None,
        status: str = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Shipment]:
        """List all shipments"""
        return shipment_crud.get_shipments(db, company_id, status, skip, limit)
    
    @staticmethod
    def create_shipment(db: Session, shipment: ShipmentCreate) -> Shipment:
        """Create shipment with validation and auto-generated ID"""
        
        if not company_crud.company_exists(db, shipment.company_id):
            raise ValueError(f"Company with ID {shipment.company_id} not found")
        
        if not user_crud.get_user(db, shipment.created_by_user_id):
            raise ValueError(f"User with ID {shipment.created_by_user_id} not found")
        
        company = company_crud.get_company(db, shipment.company_id)
        
        shipment_id = generate_shipment_id(
            company_name=company.company_name,
            shipment_name=shipment.shipment_name,
            db=db
        )
        
        # Prepare data with generated ID
        shipment_data = shipment.model_dump()
        shipment_data['shipment_id'] = shipment_id
        
        # Create shipment
        return shipment_crud.create_shipment(db, shipment_data)
    
    @staticmethod
    def update_shipment(db: Session, shipment_id: str, shipment_update: ShipmentUpdate) -> Optional[Shipment]:
        """Update shipment with validation"""
        
        # Check shipment exists
        if not shipment_crud.shipment_exists(db, shipment_id):
            raise ValueError(f"Shipment with ID {shipment_id} not found")
        
        # Update shipment
        update_data = shipment_update.model_dump(exclude_unset=True)
        return shipment_crud.update_shipment(db, shipment_id, update_data)
    
    @staticmethod
    def update_shipment_status(db: Session, shipment_id: str, new_status: str) -> Optional[Shipment]:
        """Update shipment status with validation"""
        
        # Validate status
        valid_statuses = ['draft', 'active', 'in_transit', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Check shipment exists
        if not shipment_crud.shipment_exists(db, shipment_id):
            raise ValueError(f"Shipment with ID {shipment_id} not found")
        
        # Prepare update
        update_data = {'status': new_status}
        if new_status == 'completed':
            update_data['completed_at'] = datetime.utcnow()
        
        # Update status
        return shipment_crud.update_shipment(db, shipment_id, update_data)
    
    @staticmethod
    def delete_shipment(db: Session, shipment_id: str) -> bool:
        """Delete shipment with validation"""
        
        # Check shipment exists
        if not shipment_crud.shipment_exists(db, shipment_id):
            raise ValueError(f"Shipment with ID {shipment_id} not found")
        
        # Check if shipment has files
        file_count = shipment_crud.get_shipment_file_count(db, shipment_id)
        if file_count > 0:
            raise ValueError(f"Cannot delete shipment with {file_count} documents")
        
        # Delete shipment
        return shipment_crud.delete_shipment(db, shipment_id)