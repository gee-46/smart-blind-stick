"""Safety & Emergency State Manager Service.

Handles the complete safety and emergency lifecycle:

- Manual SOS
- Fall detection
- Fall confirmation countdown
- Automatic SOS escalation
- Emergency cancellation
- Emergency resolution
- GPS location handling
- Guardian notifications
- Emergency audit logging
- Backward compatibility with the legacy SOSEvent API
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.device import Device
from app.models.event import Event, SOSEvent
from app.models.emergency import EmergencySession, EmergencyLog

from app.schemas.emergency import (
    EmergencyState,
    EmergencyTriggerType,
    NotificationStatus,
    ManualSOSRequest,
    FallDetectionRequest,
    FallAssessmentResult,
    EmergencyCancelRequest,
    EmergencyResolveRequest,
    EmergencyStatusResponse,
)

from app.services.location_service import LocationService
from app.services.fall_detection_service import FallDetectionService
from app.services.notification_service import (
    get_notification_service,
    EmergencyAlertPayload,
)


class EmergencyService:
    """Core Safety & Emergency State Manager."""

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_now() -> datetime:
        """Return current UTC time."""
        return datetime.now(timezone.utc)

    @staticmethod
    def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """Convert a datetime into a timezone-aware UTC datetime."""
        if dt is None:
            return None

        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    @staticmethod
    def _generate_session_id() -> str:
        """Generate a unique human-readable emergency session ID."""
        now = datetime.now(timezone.utc)
        short_uuid = uuid.uuid4().hex[:6].upper()

        return f"EMG-{now.strftime('%Y%m%d')}-{short_uuid}"

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    @classmethod
    def _log_audit_entry(
        cls,
        db: Session,
        device_id: str,
        session_id: Optional[str],
        previous_state: Optional[str],
        new_state: str,
        event_type: str,
        message: str,
        extra_data: Optional[dict] = None,
    ) -> EmergencyLog:
        """Persist an emergency audit log entry."""

        log_entry = EmergencyLog(
            session_id=session_id,
            device_id=device_id,
            previous_state=previous_state,
            new_state=new_state,
            event_type=event_type,
            message=message,
            extra_data=extra_data or {},
            timestamp=cls._utc_now(),
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return log_entry

    # ------------------------------------------------------------------
    # Device Handling
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_device_exists(
        cls,
        db: Session,
        device_id: str,
    ) -> Device:
        """Create a device record if the device is seen for the first time."""

        device = (
            db.query(Device)
            .filter(Device.device_id == device_id)
            .first()
        )

        if device is None:
            device = Device(
                device_id=device_id,
                battery=100.0,
                status="active",
                gps_available=True,
                last_seen=cls._utc_now(),
            )

            db.add(device)
            db.commit()
            db.refresh(device)

        return device

    # ------------------------------------------------------------------
    # Active Session
    # ------------------------------------------------------------------

    @classmethod
    def get_active_session(
        cls,
        db: Session,
        device_id: str,
    ) -> Optional[EmergencySession]:
        """Return the latest active emergency session for a device."""

        active_states = [
            EmergencyState.PENDING_CONFIRMATION.value,
            EmergencyState.ACTIVE_SOS.value,
            EmergencyState.FALL_DETECTED.value,
        ]

        session = (
            db.query(EmergencySession)
            .filter(
                EmergencySession.device_id == device_id,
                EmergencySession.state.in_(active_states),
            )
            .order_by(EmergencySession.started_at.desc())
            .first()
        )

        if session is not None:
            session = cls._check_and_escalate_if_timed_out(
                db,
                session,
            )

        return session

    # ------------------------------------------------------------------
    # Countdown / Automatic Escalation
    # ------------------------------------------------------------------

    @classmethod
    def _check_and_escalate_if_timed_out(
        cls,
        db: Session,
        session: EmergencySession,
    ) -> EmergencySession:
        """Automatically escalate a pending fall after timeout."""

        if session.state != EmergencyState.PENDING_CONFIRMATION.value:
            return session

        now = cls._utc_now()

        started_at = cls._ensure_utc(session.started_at)

        if started_at is None:
            return session

        countdown_seconds = session.countdown_seconds or 0

        elapsed_seconds = (
            now - started_at
        ).total_seconds()

        if elapsed_seconds < countdown_seconds:
            return session

        # --------------------------------------------------------------
        # Countdown expired
        # --------------------------------------------------------------

        previous_state = session.state

        session.state = EmergencyState.ACTIVE_SOS.value
        session.confirmed_at = now

        # --------------------------------------------------------------
        # Resolve latest GPS location
        # --------------------------------------------------------------

        if session.latitude is None or session.longitude is None:
            (
                latitude,
                longitude,
                _is_mock,
                maps_url,
            ) = LocationService.get_latest_location(
                db,
                session.device_id,
            )

            session.latitude = latitude
            session.longitude = longitude
            session.maps_url = maps_url

        # --------------------------------------------------------------
        # Send guardian notification
        # --------------------------------------------------------------

        settings = get_settings()
        notifier = get_notification_service()

        alert_payload = EmergencyAlertPayload(
            device_id=session.device_id,
            guardian_name=settings.GUARDIAN_NAME,
            emergency_type=EmergencyTriggerType.AUTOMATIC_FALL.value,
            title=(
                f"AUTOMATIC SOS - Fall Detected "
                f"on Stick {session.device_id}"
            ),
            message=(
                f"A fall was detected on Smart Stick "
                f"{session.device_id}. "
                f"The {countdown_seconds}-second confirmation "
                f"window expired without cancellation. "
                f"Immediate assistance may be required."
            ),
            latitude=session.latitude,
            longitude=session.longitude,
            maps_url=session.maps_url,
            timestamp=now,
            extra_details={
                "session_id": session.session_id,
                "fall_confidence": session.fall_confidence,
                "auto_escalated": True,
            },
        )

        notification_result = notifier.send_emergency_alert(
            alert_payload
        )

        session.notification_status = (
            NotificationStatus.DISPATCHED.value
            if notification_result.success
            else NotificationStatus.FAILED.value
        )

        session.notification_details = (
            notification_result.model_dump(mode="json")
        )

        db.commit()
        db.refresh(session)

        # --------------------------------------------------------------
        # Audit log
        # --------------------------------------------------------------

        cls._log_audit_entry(
            db=db,
            device_id=session.device_id,
            session_id=session.session_id,
            previous_state=previous_state,
            new_state=EmergencyState.ACTIVE_SOS.value,
            event_type="AUTO_SOS_ESCALATION",
            message=(
                f"Fall confirmation countdown of "
                f"{countdown_seconds} seconds expired. "
                f"Emergency automatically escalated to ACTIVE_SOS."
            ),
            extra_data={
                "maps_url": session.maps_url,
                "confidence": session.fall_confidence,
                "notification_success": notification_result.success,
            },
        )

        # --------------------------------------------------------------
        # Generic event for other modules
        # --------------------------------------------------------------

        db_event = Event(
            device_id=session.device_id,
            source="safety_engine",
            event_type="sos",
            risk_level="critical",
            message=(
                f"Automatic SOS triggered after unconfirmed "
                f"fall on {session.device_id}"
            ),
            extra={
                "session_id": session.session_id,
                "maps_url": session.maps_url,
            },
            timestamp=now,
        )

        db.add(db_event)
        db.commit()

        return session

    # ==================================================================
    # MANUAL SOS
    # ==================================================================

    @classmethod
    def trigger_manual_sos(
        cls,
        db: Session,
        request: ManualSOSRequest,
    ) -> EmergencySession:
        """Trigger an immediate manual SOS."""

        cls._ensure_device_exists(
            db,
            request.device_id,
        )

        now = cls._utc_now()

        # --------------------------------------------------------------
        # Resolve GPS
        # --------------------------------------------------------------

        latitude = request.latitude
        longitude = request.longitude

        if latitude is None or longitude is None:
            (
                latitude,
                longitude,
                _is_mock,
                maps_url,
            ) = LocationService.get_latest_location(
                db,
                request.device_id,
            )
        else:
            LocationService.record_location(
                db,
                request.device_id,
                latitude,
                longitude,
            )

            maps_url = LocationService.format_maps_url(
                latitude,
                longitude,
            )

        # --------------------------------------------------------------
        # Check for existing emergency
        # --------------------------------------------------------------

        existing_session = (
            db.query(EmergencySession)
            .filter(
                EmergencySession.device_id == request.device_id,
                EmergencySession.state.in_([
                    EmergencyState.PENDING_CONFIRMATION.value,
                    EmergencyState.ACTIVE_SOS.value,
                ]),
            )
            .order_by(EmergencySession.started_at.desc())
            .first()
        )

        if existing_session is not None:

            previous_state = existing_session.state

            session = existing_session

            session.state = EmergencyState.ACTIVE_SOS.value
            session.trigger_type = (
                EmergencyTriggerType.MANUAL_SOS.value
            )
            session.latitude = latitude
            session.longitude = longitude
            session.maps_url = maps_url
            session.confirmed_at = now

            session_id = session.session_id

        else:

            previous_state = EmergencyState.IDLE.value
            session_id = cls._generate_session_id()

            session = EmergencySession(
                session_id=session_id,
                device_id=request.device_id,
                state=EmergencyState.ACTIVE_SOS.value,
                trigger_type=EmergencyTriggerType.MANUAL_SOS.value,
                fall_confidence=1.0,
                countdown_seconds=0,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                started_at=now,
                confirmed_at=now,
                notification_status=NotificationStatus.PENDING.value,
            )

            db.add(session)

        # --------------------------------------------------------------
        # Guardian notification
        # --------------------------------------------------------------

        settings = get_settings()
        notifier = get_notification_service()

        reason = (
            request.reason
            or "Manual SOS button pressed"
        )

        alert_payload = EmergencyAlertPayload(
            device_id=request.device_id,
            guardian_name=settings.GUARDIAN_NAME,
            emergency_type=EmergencyTriggerType.MANUAL_SOS.value,
            title=(
                f"MANUAL SOS ACTIVATED - "
                f"Stick {request.device_id}"
            ),
            message=(
                f"The user activated the physical SOS button "
                f"on Smart Stick {request.device_id}. "
                f"Reason: {reason}"
            ),
            latitude=latitude,
            longitude=longitude,
            maps_url=maps_url,
            timestamp=now,
            extra_details={
                "session_id": session_id,
                "reason": reason,
            },
        )

        notification_result = notifier.send_emergency_alert(
            alert_payload
        )

        session.notification_status = (
            NotificationStatus.DISPATCHED.value
            if notification_result.success
            else NotificationStatus.FAILED.value
        )

        session.notification_details = (
            notification_result.model_dump(mode="json")
        )

        db.commit()
        db.refresh(session)

        # --------------------------------------------------------------
        # Audit log
        # --------------------------------------------------------------

        cls._log_audit_entry(
            db=db,
            device_id=request.device_id,
            session_id=session_id,
            previous_state=previous_state,
            new_state=EmergencyState.ACTIVE_SOS.value,
            event_type="MANUAL_SOS_TRIGGERED",
            message=(
                f"Manual SOS activated by user. "
                f"Reason: {reason}"
            ),
            extra_data={
                "latitude": latitude,
                "longitude": longitude,
                "maps_url": maps_url,
            },
        )

        # --------------------------------------------------------------
        # Legacy SOSEvent
        # --------------------------------------------------------------

        legacy_sos = SOSEvent(
            device_id=request.device_id,
            reason=reason,
            latitude=latitude,
            longitude=longitude,
            notified=notification_result.success,
            timestamp=now,
        )

        db.add(legacy_sos)

        # --------------------------------------------------------------
        # Generic event
        # --------------------------------------------------------------

        event_entry = Event(
            device_id=request.device_id,
            source="safety_engine",
            event_type="sos",
            risk_level="critical",
            message=(
                f"Manual SOS emergency active "
                f"for {request.device_id}"
            ),
            extra={
                "session_id": session_id,
                "maps_url": maps_url,
            },
            timestamp=now,
        )

        db.add(event_entry)

        db.commit()

        return session

    # ==================================================================
    # FALL DETECTION
    # ==================================================================

    @classmethod
    def process_fall_detection(
        cls,
        db: Session,
        request: FallDetectionRequest,
    ) -> Tuple[
        FallAssessmentResult,
        Optional[EmergencySession],
    ]:
        """Process sensor telemetry and start fall confirmation."""

        cls._ensure_device_exists(
            db,
            request.device_id,
        )

        now = cls._utc_now()
        settings = get_settings()

        # --------------------------------------------------------------
        # Evaluate telemetry
        # --------------------------------------------------------------

        assessment = (
            FallDetectionService.evaluate_telemetry(
                telemetry=request.telemetry,
                override_confidence=request.confidence,
            )
        )

        # --------------------------------------------------------------
        # No fall detected
        # --------------------------------------------------------------

        if not assessment.detected:

            cls._log_audit_entry(
                db=db,
                device_id=request.device_id,
                session_id=None,
                previous_state=None,
                new_state=EmergencyState.IDLE.value,
                event_type="FALL_EVALUATION_NEGATIVE",
                message=(
                    "Sensor telemetry evaluated. "
                    f"No fall detected. {assessment.reason}"
                ),
                extra_data=assessment.model_dump(
                    mode="json"
                ),
            )

            return assessment, None

        # --------------------------------------------------------------
        # Resolve GPS
        # --------------------------------------------------------------

        latitude = request.latitude
        longitude = request.longitude

        if latitude is None or longitude is None:

            (
                latitude,
                longitude,
                _is_mock,
                maps_url,
            ) = LocationService.get_latest_location(
                db,
                request.device_id,
            )

        else:

            LocationService.record_location(
                db,
                request.device_id,
                latitude,
                longitude,
            )

            maps_url = LocationService.format_maps_url(
                latitude,
                longitude,
            )

        # --------------------------------------------------------------
        # Check existing emergency
        # --------------------------------------------------------------

        existing_session = (
            db.query(EmergencySession)
            .filter(
                EmergencySession.device_id == request.device_id,
                EmergencySession.state.in_([
                    EmergencyState.PENDING_CONFIRMATION.value,
                    EmergencyState.ACTIVE_SOS.value,
                ]),
            )
            .order_by(EmergencySession.started_at.desc())
            .first()
        )

        if existing_session is not None:

            # Never downgrade ACTIVE_SOS
            if (
                existing_session.state
                == EmergencyState.ACTIVE_SOS.value
            ):
                return assessment, existing_session

            session = existing_session

            previous_state = session.state

            old_confidence = (
                session.fall_confidence
                if session.fall_confidence is not None
                else 0.0
            )

            session.fall_confidence = max(
                old_confidence,
                assessment.confidence,
            )

            session.latitude = latitude
            session.longitude = longitude
            session.maps_url = maps_url

            session_id = session.session_id

        else:

            session_id = cls._generate_session_id()
            previous_state = EmergencyState.IDLE.value

            countdown_seconds = (
                settings.FALL_CONFIRMATION_TIMEOUT_SECONDS
            )

            session = EmergencySession(
                session_id=session_id,
                device_id=request.device_id,
                state=EmergencyState.PENDING_CONFIRMATION.value,
                trigger_type=(
                    EmergencyTriggerType.AUTOMATIC_FALL.value
                ),
                fall_confidence=assessment.confidence,
                countdown_seconds=countdown_seconds,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                notification_status=(
                    NotificationStatus.PENDING.value
                ),
                started_at=now,
            )

            db.add(session)

        db.commit()
        db.refresh(session)

        # --------------------------------------------------------------
        # Audit log
        # --------------------------------------------------------------

        cls._log_audit_entry(
            db=db,
            device_id=request.device_id,
            session_id=session_id,
            previous_state=previous_state,
            new_state=EmergencyState.PENDING_CONFIRMATION.value,
            event_type="FALL_DETECTED_PENDING_CONFIRMATION",
            message=(
                f"Possible fall detected. "
                f"Confidence: "
                f"{assessment.confidence * 100:.1f}%. "
                f"Confirmation window: "
                f"{session.countdown_seconds} seconds. "
                f"Reason: {assessment.reason}"
            ),
            extra_data=assessment.model_dump(
                mode="json"
            ),
        )

        # --------------------------------------------------------------
        # Generic event
        # --------------------------------------------------------------

        event_entry = Event(
            device_id=request.device_id,
            source="safety_engine",
            event_type="fall",
            risk_level="high",
            message=(
                f"Fall detected on stick "
                f"{request.device_id}. "
                f"Awaiting user confirmation."
            ),
            extra={
                "session_id": session_id,
                "confidence": assessment.confidence,
            },
            timestamp=now,
        )

        db.add(event_entry)
        db.commit()

        return assessment, session

    # ==================================================================
    # CANCEL EMERGENCY
    # ==================================================================

    @classmethod
    def cancel_emergency(
        cls,
        db: Session,
        request: EmergencyCancelRequest,
    ) -> Optional[EmergencySession]:
        """Cancel an active or pending emergency."""

        now = cls._utc_now()

        query = (
            db.query(EmergencySession)
            .filter(
                EmergencySession.device_id
                == request.device_id
            )
        )

        if request.session_id:

            query = query.filter(
                EmergencySession.session_id
                == request.session_id
            )

        else:

            query = query.filter(
                EmergencySession.state.in_([
                    EmergencyState.PENDING_CONFIRMATION.value,
                    EmergencyState.ACTIVE_SOS.value,
                    EmergencyState.FALL_DETECTED.value,
                ])
            )

        session = (
            query
            .order_by(EmergencySession.started_at.desc())
            .first()
        )

        if session is None:
            return None

        previous_state = session.state

        session.state = EmergencyState.CANCELLED.value
        session.cancellation_reason = (
            request.reason
        )
        session.cancelled_at = now

        # --------------------------------------------------------------
        # Cancellation notification
        # --------------------------------------------------------------

        if (
            session.notification_status
            == NotificationStatus.DISPATCHED.value
        ):

            settings = get_settings()
            notifier = get_notification_service()

            cancel_payload = EmergencyAlertPayload(
                device_id=session.device_id,
                guardian_name=settings.GUARDIAN_NAME,
                emergency_type=session.trigger_type,
                title=(
                    f"EMERGENCY CANCELLED - "
                    f"Stick {session.device_id}"
                ),
                message=(
                    f"The emergency alert on stick "
                    f"{session.device_id} was cancelled "
                    f"by the user. "
                    f"Reason: {request.reason}"
                ),
                latitude=session.latitude,
                longitude=session.longitude,
                maps_url=session.maps_url,
                timestamp=now,
                extra_details={
                    "session_id": session.session_id,
                    "reason": request.reason,
                },
            )

            # Call only if the adapter supports it
            if hasattr(
                notifier,
                "send_cancellation_notice",
            ):
                notifier.send_cancellation_notice(
                    cancel_payload
                )

        session.notification_status = (
            NotificationStatus.CANCELLED.value
        )

        db.commit()
        db.refresh(session)

        # --------------------------------------------------------------
        # Calculate duration safely
        # --------------------------------------------------------------

        started_at = cls._ensure_utc(
            session.started_at
        )

        duration_seconds = 0

        if started_at is not None:
            duration_seconds = max(
                0,
                (now - started_at).total_seconds(),
            )

        # --------------------------------------------------------------
        # Audit log
        # --------------------------------------------------------------

        cls._log_audit_entry(
            db=db,
            device_id=session.device_id,
            session_id=session.session_id,
            previous_state=previous_state,
            new_state=EmergencyState.CANCELLED.value,
            event_type="EMERGENCY_CANCELLED_BY_USER",
            message=(
                f"Emergency cancelled. "
                f"Reason: {request.reason}"
            ),
            extra_data={
                "reason": request.reason,
                "duration_seconds": duration_seconds,
            },
        )

        # --------------------------------------------------------------
        # Generic event
        # --------------------------------------------------------------

        event_entry = Event(
            device_id=session.device_id,
            source="safety_engine",
            event_type="danger",
            risk_level="low",
            message=(
                f"Emergency alert cancelled by user "
                f"on stick {session.device_id}"
            ),
            extra={
                "session_id": session.session_id,
                "reason": request.reason,
            },
            timestamp=now,
        )

        db.add(event_entry)
        db.commit()

        return session

    # ==================================================================
    # RESOLVE EMERGENCY
    # ==================================================================

    @classmethod
    def resolve_emergency(
        cls,
        db: Session,
        request: EmergencyResolveRequest,
    ) -> Optional[EmergencySession]:
        """Mark an emergency as resolved."""

        now = cls._utc_now()

        query = (
            db.query(EmergencySession)
            .filter(
                EmergencySession.device_id
                == request.device_id
            )
        )

        if request.session_id:

            query = query.filter(
                EmergencySession.session_id
                == request.session_id
            )

        else:

            query = query.filter(
                EmergencySession.state.in_([
                    EmergencyState.ACTIVE_SOS.value,
                    EmergencyState.PENDING_CONFIRMATION.value,
                ])
            )

        session = (
            query
            .order_by(EmergencySession.started_at.desc())
            .first()
        )

        if session is None:
            return None

        previous_state = session.state

        session.state = EmergencyState.RESOLVED.value
        session.resolution_notes = (
            request.resolution_notes
        )
        session.resolved_at = now

        # --------------------------------------------------------------
        # Guardian resolution notification
        # --------------------------------------------------------------

        settings = get_settings()
        notifier = get_notification_service()

        resolve_payload = EmergencyAlertPayload(
            device_id=session.device_id,
            guardian_name=settings.GUARDIAN_NAME,
            emergency_type=session.trigger_type,
            title=(
                f"EMERGENCY RESOLVED - "
                f"Stick {session.device_id}"
            ),
            message=(
                f"The emergency for stick "
                f"{session.device_id} has been resolved. "
                f"Notes: {request.resolution_notes}"
            ),
            latitude=session.latitude,
            longitude=session.longitude,
            maps_url=session.maps_url,
            timestamp=now,
            extra_details={
                "session_id": session.session_id,
                "notes": request.resolution_notes,
            },
        )

        if hasattr(
            notifier,
            "send_resolution_notice",
        ):
            notifier.send_resolution_notice(
                resolve_payload
            )

        db.commit()
        db.refresh(session)

        # --------------------------------------------------------------
        # Audit log
        # --------------------------------------------------------------

        cls._log_audit_entry(
            db=db,
            device_id=session.device_id,
            session_id=session.session_id,
            previous_state=previous_state,
            new_state=EmergencyState.RESOLVED.value,
            event_type="EMERGENCY_RESOLVED",
            message=(
                f"Emergency marked resolved. "
                f"Notes: {request.resolution_notes}"
            ),
            extra_data={
                "notes": request.resolution_notes,
            },
        )

        # --------------------------------------------------------------
        # Generic event
        # --------------------------------------------------------------

        event_entry = Event(
            device_id=session.device_id,
            source="safety_engine",
            event_type="resolution",
            risk_level="low",
            message=(
                f"Emergency resolved for "
                f"{session.device_id}"
            ),
            extra={
                "session_id": session.session_id,
                "notes": request.resolution_notes,
            },
            timestamp=now,
        )

        db.add(event_entry)
        db.commit()

        return session

    # ==================================================================
    # EMERGENCY STATUS
    # ==================================================================

    @classmethod
    def get_emergency_status(
        cls,
        db: Session,
        device_id: str,
    ) -> EmergencyStatusResponse:
        """Return the current emergency status of a device."""

        active_session = cls.get_active_session(
            db,
            device_id,
        )

        # --------------------------------------------------------------
        # No active emergency
        # --------------------------------------------------------------

        if active_session is None:

            (
                latitude,
                longitude,
                _is_mock,
                maps_url,
            ) = LocationService.get_latest_location(
                db,
                device_id,
                fallback_to_mock=False,
            )

            return EmergencyStatusResponse(
                device_id=device_id,
                has_active_emergency=False,
                state=EmergencyState.IDLE,
                active_session_id=None,
                trigger_type=None,
                countdown_remaining_seconds=None,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                notification_status=NotificationStatus.NONE.value,
                message=(
                    "Device is operating normally. "
                    "No active emergency."
                ),
            )

        # --------------------------------------------------------------
        # Calculate countdown
        # --------------------------------------------------------------

        countdown_remaining = None

        if (
            active_session.state
            == EmergencyState.PENDING_CONFIRMATION.value
        ):

            now = cls._utc_now()

            started_at = cls._ensure_utc(
                active_session.started_at
            )

            if started_at is not None:

                elapsed = (
                    now - started_at
                ).total_seconds()

                countdown_seconds = (
                    active_session.countdown_seconds
                    or 0
                )

                countdown_remaining = max(
                    0,
                    int(
                        countdown_seconds
                        - elapsed
                    ),
                )

        # --------------------------------------------------------------
        # Status message
        # --------------------------------------------------------------

        status_message = (
            f"Active emergency in state "
            f"'{active_session.state}' "
            f"(Trigger: "
            f"{active_session.trigger_type})"
        )

        if countdown_remaining is not None:

            status_message += (
                f" - {countdown_remaining}s "
                f"remaining before automatic SOS."
            )

        # --------------------------------------------------------------
        # Return response
        # --------------------------------------------------------------

        return EmergencyStatusResponse(
            device_id=device_id,
            has_active_emergency=True,
            state=EmergencyState(
                active_session.state
            ),
            active_session_id=(
                active_session.session_id
            ),
            trigger_type=EmergencyTriggerType(
                active_session.trigger_type
            ),
            countdown_remaining_seconds=(
                countdown_remaining
            ),
            latitude=active_session.latitude,
            longitude=active_session.longitude,
            maps_url=active_session.maps_url,
            notification_status=(
                active_session.notification_status
            ),
            message=status_message,
        )

    # ==================================================================
    # EMERGENCY AUDIT LOGS
    # ==================================================================

    @staticmethod
    def get_emergency_logs(
        db: Session,
        device_id: str,
        limit: int = 50,
    ) -> List[EmergencyLog]:
        """Return emergency audit logs for a device."""

        limit = max(
            1,
            min(limit, 500),
        )

        return (
            db.query(EmergencyLog)
            .filter(
                EmergencyLog.device_id == device_id
            )
            .order_by(
                EmergencyLog.timestamp.desc()
            )
            .limit(limit)
            .all()
        )