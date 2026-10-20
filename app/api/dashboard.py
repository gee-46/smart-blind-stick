"""Guardian Live Monitoring Web Dashboard.

Provides a real-time web interface for caregivers, guardians, and hardware testers
to monitor the Smart Blind Stick's GPS location, battery, obstacle detections,
emergency state, and live sensor telemetry.
Redesigned with the Obsidian Signal visual identity, cinematic loader, and QR mobile access.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.api.guardian_ui import generate_guardian_html

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the Guardian live monitoring web application."""
    return HTMLResponse(content=generate_guardian_html(
        title="🦯 Smart Blind Stick - Guardian Live Monitor",
        is_pwa=False
    ))
