from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import ShipmentCreate, ShipmentUpdate, ShipmentResponse
from services import ShipmentService

router = APIRouter()

@router.get("/", response_model=List[ShipmentResponse])
def list_shipments(
    company_id: str = None,
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all shipments with optional filters"""
    return ShipmentService.list_shipments(db, company_id, status_filter, skip, limit)

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    """Get a specific shipment by ID"""
    shipment = ShipmentService.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment

@router.post("/", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    """Create a new shipment"""
    try:
        return ShipmentService.create_shipment(db, shipment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{shipment_id}", response_model=ShipmentResponse)
def update_shipment(shipment_id: str, shipment_update: ShipmentUpdate, db: Session = Depends(get_db)):
    """Update a shipment"""
    try:
        shipment = ShipmentService.update_shipment(db, shipment_id, shipment_update)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
        return shipment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/{shipment_id}/status")
def update_shipment_status(shipment_id: str, status: str, db: Session = Depends(get_db)):
    """Update shipment status"""
    try:
        shipment = ShipmentService.update_shipment_status(db, shipment_id, status)
        return {"message": f"Shipment status updated to {status}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shipment(shipment_id: str, db: Session = Depends(get_db)):
    """Delete a shipment"""
    try:
        if not ShipmentService.delete_shipment(db, shipment_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))