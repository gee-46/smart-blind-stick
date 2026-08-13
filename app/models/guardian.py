"""
Guardian ORM models.

Adds the account + ownership layer the mobile app needs on top of the
existing Device/Location/Event/SOSEvent tables:

    Guardian            -- a person who monitors one or more sticks
    GuardianDevice       -- ownership/pairing link between a Guardian and a Device
    EmergencyContact     -- a guardian's emergency contacts (persisted, not local-only)
    PushToken            -- an Expo push token registered by a guardian's phone

None of the existing tables (Device, Location, Event, SOSEvent) are
modified -- this is purely additive.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Guardian(Base):
    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    devices: Mapped[list["GuardianDevice"]] = relationship(
        "GuardianDevice", back_populates="guardian", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["EmergencyContact"]] = relationship(
        "EmergencyContact", back_populates="guardian", cascade="all, delete-orphan"
    )
    push_tokens: Mapped[list["PushToken"]] = relationship(
        "PushToken", back_populates="guardian", cascade="all, delete-orphan"
    )


class GuardianDevice(Base):
    """
    Ownership/pairing link. A guardian pairs a device by device_id; this
    row is the real backend record of that relationship (not a local-only
    mobile setting).
    """

    __tablename__ = "guardian_devices"
    __table_args__ = (
        UniqueConstraint("guardian_id", "device_id", name="uq_guardian_device"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guardian_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("guardians.id"), index=True, nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary_guardian: Mapped[bool] = mapped_column(Boolean, default=True)

    paired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="devices")
    device: Mapped["Device"] = relationship("Device")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guardian_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("guardians.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    relationship_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="contacts")


class PushToken(Base):
    """
    Expo push token registered by a guardian's device (phone), so the
    notification service has somewhere real to send to. Distinct from
    `Device` (the smart stick) -- this is the *guardian's phone*.
    """

    __tablename__ = "push_tokens"
    __table_args__ = (
        UniqueConstraint("guardian_id", "expo_push_token", name="uq_guardian_push_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    guardian_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("guardians.id"), index=True, nullable=False
    )
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expo_push_token: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="push_tokens")
