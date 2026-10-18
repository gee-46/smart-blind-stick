"""Safety & Emergency API Endpoints.

Dedicated controller for Member 3's Safety & Emergency subsystem:
- POST /api/emergency/sos/manual
- POST /api/emergency/fall/detect
- POST /api/emergency/sos/cancel
- POST /api/emergency/sos/resolve
- GET /api/emergency/status/{device_id}
- GET /api/emergency/logs/{device_id}
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.emergency import (
    ManualSOSRequest,
    FallDetectionRequest,
    FallAssessmentResult,
    EmergencyCancelRequest,
    EmergencyResolveRequest,
    EmergencySessionResponse,
    EmergencyStatusResponse,
    EmergencyLogResponse,
    EmergencyLogListResponse,
    EmergencyState,
    EmergencyTriggerType,
)
from app.services.emergency_service import EmergencyService

router = APIRouter(prefix="/api/emergency", tags=["Safety & Emergency"])


@router.post(
    "/sos/manual",
    response_model=EmergencySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Manual SOS",
    description="Immediately activates ACTIVE_SOS state, captures latest GPS, notifies guardian, and logs emergency."
)
def trigger_manual_sos(
    payload: ManualSOSRequest,
    db: Session = Depends(get_db)
):
    """Execute immediate Manual SOS workflow."""
    session = EmergencyService.trigger_manual_sos(db, payload)
    return EmergencySessionResponse(
        session_id=session.session_id,
        device_id=session.device_id,
        state=EmergencyState(session.state),
        trigger_type=EmergencyTriggerType(session.trigger_type),
        fall_confidence=session.fall_confidence,
        countdown_remaining_seconds=0,
        latitude=session.latitude,
        longitude=session.longitude,
        maps_url=session.maps_url,
        notification_status=session.notification_status,
        cancellation_reason=session.cancellation_reason,
        resolution_notes=session.resolution_notes,
        started_at=session.started_at,
        confirmed_at=session.confirmed_at,
        cancelled_at=session.cancelled_at,
        resolved_at=session.resolved_at,
    )


@router.post(
    "/fall/detect",
    summary="Report & Assess Fall Telemetry",
    description="Evaluates multi-condition IMU telemetry. If fall is confirmed, enters PENDING_CONFIRMATION countdown."
)
def report_fall_telemetry(
    payload: FallDetectionRequest,
    db: Session = Depends(get_db)
):
    """Assess sensor readings and initiate confirmation window if fall detected."""
    assessment, session = EmergencyService.process_fall_detection(db, payload)
    
    session_response = None
    if session:
        session_response = EmergencySessionResponse(
            session_id=session.session_id,
            device_id=session.device_id,
            state=EmergencyState(session.state),
            trigger_type=EmergencyTriggerType(session.trigger_type),
            fall_confidence=session.fall_confidence,
            countdown_remaining_seconds=session.countdown_seconds,
            latitude=session.latitude,
            longitude=session.longitude,
            maps_url=session.maps_url,
            notification_status=session.notification_status,
            cancellation_reason=session.cancellation_reason,
            resolution_notes=session.resolution_notes,
            started_at=session.started_at,
            confirmed_at=session.confirmed_at,
            cancelled_at=session.cancelled_at,
            resolved_at=session.resolved_at,
        )

    return {
        "status": "fall_detected" if assessment.detected else "no_fall",
        "assessment": assessment,
        "session": session_response,
    }


@router.post(
    "/sos/cancel",
    response_model=EmergencySessionResponse,
    summary="Cancel False Alarm / Emergency",
    description="Allows user to cancel a pending fall confirmation or active SOS within window."
)
def cancel_emergency(
    payload: EmergencyCancelRequest,
    db: Session = Depends(get_db)
):
    """Cancel an active or pending emergency session."""
    session = EmergencyService.cancel_emergency(db, payload)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active or pending emergency session found to cancel for device '{payload.device_id}'"
        )
    return EmergencySessionResponse(
        session_id=session.session_id,
        device_id=session.device_id,
        state=EmergencyState(session.state),
        trigger_type=EmergencyTriggerType(session.trigger_type),
        fall_confidence=session.fall_confidence,
        countdown_remaining_seconds=None,
        latitude=session.latitude,
        longitude=session.longitude,
        maps_url=session.maps_url,
        notification_status=session.notification_status,
        cancellation_reason=session.cancellation_reason,
        resolution_notes=session.resolution_notes,
        started_at=session.started_at,
        confirmed_at=session.confirmed_at,
        cancelled_at=session.cancelled_at,
        resolved_at=session.resolved_at,
    )


@router.post(
    "/sos/resolve",
    response_model=EmergencySessionResponse,
    summary="Resolve Emergency",
    description="Marks an active emergency as resolved after guardian assistance or user safety confirmed."
)
def resolve_emergency(
    payload: EmergencyResolveRequest,
    db: Session = Depends(get_db)
):
    """Resolve an ongoing emergency."""
    session = EmergencyService.resolve_emergency(db, payload)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active emergency session found to resolve for device '{payload.device_id}'"
        )
    return EmergencySessionResponse(
        session_id=session.session_id,
        device_id=session.device_id,
        state=EmergencyState(session.state),
        trigger_type=EmergencyTriggerType(session.trigger_type),
        fall_confidence=session.fall_confidence,
        countdown_remaining_seconds=None,
        latitude=session.latitude,
        longitude=session.longitude,
        maps_url=session.maps_url,
        notification_status=session.notification_status,
        cancellation_reason=session.cancellation_reason,
        resolution_notes=session.resolution_notes,
        started_at=session.started_at,
        confirmed_at=session.confirmed_at,
        cancelled_at=session.cancelled_at,
        resolved_at=session.resolved_at,
    )


@router.get(
    "/status/{device_id}",
    response_model=EmergencyStatusResponse,
    summary="Get Device Emergency Status",
    description="Returns real-time emergency state, pending countdown remaining, coordinates, and notification status."
)
def get_emergency_status(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Query current emergency state for a device."""
    return EmergencyService.get_emergency_status(db, device_id)


@router.get(
    "/logs/{device_id}",
    response_model=EmergencyLogListResponse,
    summary="Get Emergency Audit Trail",
    description="Retrieves chronological immutable emergency audit logs for a device."
)
def get_emergency_logs(
    device_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Query emergency audit trail for a device."""
    logs = EmergencyService.get_emergency_logs(db, device_id, limit=limit)
    response_logs = [
        EmergencyLogResponse(
            id=log.id,
            session_id=log.session_id,
            device_id=log.device_id,
            previous_state=log.previous_state,
            new_state=log.new_state,
            event_type=log.event_type,
            message=log.message,
            extra_data=log.extra_data,
            timestamp=log.timestamp,
        )
        for log in logs
    ]
    return EmergencyLogListResponse(
        device_id=device_id,
        count=len(response_logs),
        logs=response_logs,
    )
