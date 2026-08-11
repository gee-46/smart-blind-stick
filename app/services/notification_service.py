"""
Notification service abstraction.

For now only a mock implementation exists (it just logs). This is the
seam where real notification channels get plugged in later without
touching the SOS API or any calling code:

    NotificationService (interface)
            |
            +-- MockNotificationService   (implemented now)
            |
            +-- Future:
                  - SmsNotificationService
                  - FirebaseNotificationService
                  - WhatsAppNotificationService

`get_notification_service()` is the single place that decides which
implementation is active, so swapping providers is a one-line change.
"""
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("notification_service")


class NotificationService(ABC):
    @abstractmethod
    def send_sos_alert(self, device_id: str, reason: str, latitude: float | None, longitude: float | None) -> bool:
        """Send an SOS alert. Returns True if the alert was dispatched."""
        raise NotImplementedError


class MockNotificationService(NotificationService):
    """
    Development/testing implementation. Does not call any paid SMS,
    push-notification, or messaging provider. It only logs what WOULD be
    sent, so the rest of the system can be built and tested end-to-end
    before a real provider is integrated.
    """

    def send_sos_alert(self, device_id: str, reason: str, latitude: float | None, longitude: float | None) -> bool:
        logger.warning(
            "[MOCK SOS ALERT] device=%s reason=%s location=(%s, %s)",
            device_id,
            reason,
            latitude,
            longitude,
        )
        return True


def get_notification_service() -> NotificationService:
    # Swap this out for a real implementation later, e.g.:
    #   return SmsNotificationService(...)
    return MockNotificationService()
