"""Sensor Fusion API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.sensor_fusion import SensorReadingIn, SensorFusionResult
from app.services.sensor_fusion_service import SensorFusionService

router = APIRouter(prefix="/api/sensors", tags=["sensor_fusion"])


@router.post("/data", response_model=SensorFusionResult)
def ingest_sensor_readings(reading: SensorReadingIn, db: Session = Depends(get_db)):
    """
    Ingest ultrasonic and physical sensor telemetry directly from hardware.
    Evaluates obstacle risk and returns haptic/buzzer feedback commands.
    """
    return SensorFusionService.evaluate_sensors(db, reading)
