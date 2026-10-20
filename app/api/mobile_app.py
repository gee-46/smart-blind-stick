"""Mobile App Frontend (PWA) & Smart Blind Stick Companion.

Complete Feature Implementation covering all 23 features in 6 categories:
1. Core Safety Features (Features 1-5): Real-Time Obstacle Detection, Multi-Level Obstacle Detection, Sensor Fusion, Alert Prioritization, Haptic Feedback
2. AI & Intelligent Features (Features 6-10): AI Object Recognition, Type Classification, Moving Object Detection, Fall Detection, Intelligent SOS
3. Navigation Features (Features 11-13): Voice Navigation, Safe Route Recommendation, Geofencing
4. Personalization Features (Features 14-15): Adaptive Alerts, User Profiles
5. Mobile & Monitoring (Features 16-18): Live Stick Dashboard, Guardian Dashboard, Incident History
6. Reliability & Innovation (Features 19-23): Hazard Mapping, AI Assistant, Offline Safety Mode, Battery Intelligence, Self-Diagnostics

Redesigned with the 'Obsidian Signal' design system, cinematic pre-launch loader, and QR scanner access.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response, JSONResponse
import socket
from app.api.guardian_ui import generate_guardian_html

router = APIRouter(tags=["mobile_app"])


def get_local_ip() -> str:
    """Detect LAN IPv4 address of this host."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


MANIFEST_JSON = """{
  "name": "Sightline Guardian - Smart Blind Stick",
  "short_name": "SmartStick",
  "description": "Assistive Mobility & Guardian Companion for Smart Blind Stick",
  "start_url": "/app",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#F6F5EF",
  "theme_color": "#173C35",
  "icons": [
    {
      "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='48' fill='%23173C35' stroke='%233E7569' stroke-width='4'/%3E%3Ctext x='50' y='65' font-size='48' text-anchor='middle' fill='%23FFFFFF'%3E🦯%3C/text%3E%3C/svg%3E",
      "sizes": "192x192 512x512",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}"""

SERVICE_WORKER_JS = """// Smart Blind Stick PWA Service Worker - Obsidian Signal
const CACHE_NAME = 'sightline-guardian-v4';
const ASSETS = [
  '/app',
  '/manifest.json',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) {
    e.respondWith(fetch(e.request));
    return;
  }
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
"""


@router.get("/app", response_class=HTMLResponse)
def serve_mobile_app():
    """Serve the Progressive Web App (PWA) Mobile Application."""
    return HTMLResponse(content=generate_guardian_html(
        title="🦯 Smart Blind Stick - Sightline Guardian Companion",
        is_pwa=True
    ))


@router.get("/manifest.json")
def serve_manifest():
    """Serve the Web App Manifest for Android PWA installation."""
    return Response(content=MANIFEST_JSON, media_type="application/manifest+json")


@router.get("/sw.js")
def serve_service_worker():
    """Serve the Service Worker for offline capabilities."""
    return Response(content=SERVICE_WORKER_JS, media_type="application/javascript")


@router.get("/api/network-info")
def get_network_info():
    """Return host PC network interfaces and direct URL for Android phones."""
    local_ip = get_local_ip()
    port = 8000
    mobile_url = f"http://{local_ip}:{port}/app"
    dashboard_url = f"http://{local_ip}:{port}/dashboard"
    return {
        "local_ip": local_ip,
        "port": port,
        "mobile_app_url": mobile_url,
        "dashboard_url": dashboard_url,
        "qr_code_data": mobile_url,
    }
