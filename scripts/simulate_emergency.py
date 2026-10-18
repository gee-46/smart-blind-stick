"""Safety & Emergency Interactive Simulator.

Demonstrates all Member 3 capabilities for project presentation & testing without physical hardware:
1. Manual SOS button trigger & immediate escalation
2. GPS location bundling & Google Maps URL generation
3. Guardian notification dispatch (Mock/SMS/Firebase)
4. Resolving an active emergency
5. Multi-condition Fall Detection (IMU accelerometer & tilt simulation)
6. Fall confirmation countdown window
7. False-alarm cancellation by user
8. Countdown expiration and automatic SOS escalation
9. Real-time Emergency Status monitoring
10. Immutable Emergency Audit Trail inspection

Usage:
    python scripts/simulate_emergency.py --demo            # Automated end-to-end demonstration
    python scripts/simulate_emergency.py                   # Interactive menu mode
    python scripts/simulate_emergency.py --base-url http://127.0.0.1:8000
"""
import argparse
import sys
import time
import requests

# Ensure safe UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BANNER = """
========================================================================
[STICK] SMART BLIND STICK - SAFETY & EMERGENCY SUBSYSTEM SIMULATOR
        Final-Year Project Simulation & Demonstration Tool (Member 3)
========================================================================
"""


class EmergencySimulator:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", device_id: str = "STICK_001"):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id

    def _print_header(self, title: str):
        print("\n" + "=" * 70)
        print(f">> {title}")
        print("=" * 70)

    def _check_health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def demo_manual_sos(self):
        """Scenario 1: User presses physical SOS button."""
        self._print_header("SCENARIO 1: Immediate Manual SOS Activation")
        print(f"-> Simulating user pressing physical SOS button on stick '{self.device_id}'...")
        
        payload = {
            "device_id": self.device_id,
            "latitude": 12.971600,
            "longitude": 77.594600,
            "reason": "Blind user requested immediate emergency assistance (Manual Button Pressed)",
        }
        res = requests.post(f"{self.base_url}/api/emergency/sos/manual", json=payload)
        data = res.json()
        print(f"[OK] Response Status: {res.status_code}")
        print(f"   Session ID       : {data.get('session_id')}")
        print(f"   State            : {data.get('state')}")
        print(f"   Trigger Type     : {data.get('trigger_type')}")
        print(f"   GPS Coordinates  : Lat {data.get('latitude')}, Lon {data.get('longitude')}")
        print(f"   Google Maps Link : {data.get('maps_url')}")
        print(f"   Notification     : {data.get('notification_status')}")

        # Check status
        print("\n[?] Checking live device status...")
        st = requests.get(f"{self.base_url}/api/emergency/status/{self.device_id}").json()
        print(f"   Live State: {st.get('state')} | Active: {st.get('has_active_emergency')}")

        # Resolve emergency
        print("\n-> Resolving emergency (Guardian arrived)...")
        res_resolve = requests.post(
            f"{self.base_url}/api/emergency/sos/resolve",
            json={"device_id": self.device_id, "resolution_notes": "Guardian located user safely"}
        )
        print(f"[OK] Resolved: {res_resolve.json().get('state')}")

    def demo_fall_cancellation(self):
        """Scenario 2: Fall detected, but user cancels (False Alarm)."""
        self._print_header("SCENARIO 2: Fall Detection -> Cancellation (False Alarm)")
        print(f"-> Simulating IMU sensor readings during a minor stumble / dropped stick...")
        
        fall_payload = {
            "device_id": self.device_id,
            "telemetry": {
                "accel_x": 0.40,
                "accel_y": 0.75,
                "accel_z": 2.80,
                "impact_magnitude_g": 2.92,
                "tilt_angle_deg": 68.0,
                "immobility_seconds": 3.5,
                "free_fall_detected": True,
            },
            "latitude": 12.972200,
            "longitude": 77.595100,
            "reason": "Multi-condition fall criteria satisfied",
        }
        res = requests.post(f"{self.base_url}/api/emergency/fall/detect", json=fall_payload)
        data = res.json()
        print(f"[OK] Fall Assessment Status: {data.get('status')}")
        assess = data.get("assessment", {})
        print(f"   Confidence Score : {assess.get('confidence') * 100:.1f}%")
        print(f"   Assessment Reason: {assess.get('reason')}")
        session = data.get("session") or {}
        print(f"   Emergency State  : {session.get('state')}")
        print(f"   Countdown Window : {session.get('countdown_remaining_seconds')} seconds")

        print("\n[User is conscious and presses 'I AM OKAY' button within window...]")
        time.sleep(1)

        cancel_res = requests.post(
            f"{self.base_url}/api/emergency/sos/cancel",
            json={"device_id": self.device_id, "reason": "User dropped stick accidentally, user is unhurt"}
        )
        c_data = cancel_res.json()
        print(f"[OK] Emergency Cancelled: State={c_data.get('state')}, Reason='{c_data.get('cancellation_reason')}'")

    def demo_fall_auto_escalation(self):
        """Scenario 3: Fall detected, user unresponsive -> Auto-escalates to ACTIVE SOS."""
        self._print_header("SCENARIO 3: Fall Detection -> Timeout Expiry -> Automatic SOS Escalation")
        print(f"-> Simulating severe fall with unconscious/unresponsive user...")

        fall_payload = {
            "device_id": self.device_id,
            "telemetry": {
                "accel_x": 0.50,
                "accel_y": 0.90,
                "accel_z": 3.20,
                "impact_magnitude_g": 3.36,
                "tilt_angle_deg": 75.0,
                "immobility_seconds": 5.0,
                "free_fall_detected": True,
            },
            "latitude": 12.973000,
            "longitude": 77.596000,
            "reason": "Severe impact and prolonged immobility detected",
        }
        res = requests.post(f"{self.base_url}/api/emergency/fall/detect", json=fall_payload)
        session = res.json().get("session") or {}
        print(f"[!] Initial State: {session.get('state')} (Awaiting response...)")

        print("\n[Simulating countdown progression...]")
        for remaining in [15, 10, 5, 0]:
            print(f"   ... Waiting ({remaining}s remaining) ...")
            time.sleep(0.5)

        # Query status to trigger auto-escalation check
        status_res = requests.get(f"{self.base_url}/api/emergency/status/{self.device_id}").json()
        print(f"\n[ALERT] Current Status after timeout:")
        print(f"   State            : {status_res.get('state')}")
        print(f"   Trigger Type     : {status_res.get('trigger_type')}")
        print(f"   Notification     : {status_res.get('notification_status')}")
        print(f"   Google Maps Link : {status_res.get('maps_url')}")
        print(f"   System Message   : {status_res.get('message')}")

        # Clean up by resolving
        requests.post(
            f"{self.base_url}/api/emergency/sos/resolve",
            json={"device_id": self.device_id, "resolution_notes": "First responders arrived"}
        )
        print("[OK] Emergency resolved after simulation.")

    def demo_audit_trail(self):
        """Scenario 4: View immutable audit logs."""
        self._print_header("SCENARIO 4: Emergency Audit Logs & Forensic Trail")
        logs_res = requests.get(f"{self.base_url}/api/emergency/logs/{self.device_id}?limit=10").json()
        print(f"[LOG] Found {logs_res.get('count')} audit entries for stick '{self.device_id}':\n")
        for log in logs_res.get("logs", []):
            ts = log.get("timestamp")
            print(f"  [{ts}] {log.get('event_type'):<35} | {log.get('previous_state')} -> {log.get('new_state')}")
            print(f"    └─ Message: {log.get('message')}\n")

    def run_automated_demo(self):
        """Run complete end-to-end demo sequence."""
        print(BANNER)
        if not self._check_health():
            print(f"[ERROR] Backend server is not running at {self.base_url}!")
            print("-> Please start the backend with: python run.py\n")
            sys.exit(1)

        print(f"[INFO] Connected to backend at {self.base_url}")
        print(f"[INFO] Testing with simulated Device ID: {self.device_id}\n")

        self.demo_manual_sos()
        time.sleep(1)
        self.demo_fall_cancellation()
        time.sleep(1)
        self.demo_fall_auto_escalation()
        time.sleep(1)
        self.demo_audit_trail()

        print("\n" + "=" * 70)
        print("[SUCCESS] ALL SAFETY & EMERGENCY SIMULATION SCENARIOS COMPLETED!")
        print("========================================================================\n")

    def run_interactive_menu(self):
        """Interactive console interface."""
        print(BANNER)
        if not self._check_health():
            print(f"[ERROR] Backend server is not running at {self.base_url}!")
            print("-> Please start the backend with: python run.py\n")
            sys.exit(1)

        while True:
            print("\n---------------- MENU OPTIONS ----------------")
            print("1. Trigger Manual SOS (Immediate Escalation)")
            print("2. Simulate Fall Detection (High Impact + Tilt)")
            print("3. Simulate Normal Walking (Negative Fall Test)")
            print("4. Cancel Pending / Active Emergency (False Alarm)")
            print("5. Resolve Active Emergency")
            print("6. Check Live Emergency Status")
            print("7. View Emergency Audit Logs")
            print("8. Run Complete Automated Demonstration")
            print("0. Exit")
            print("----------------------------------------------")

            choice = input("Select an option (0-8): ").strip()
            if choice == "0":
                print("Exiting simulator. Goodbye!")
                break
            elif choice == "1":
                self.demo_manual_sos()
            elif choice == "2":
                self.demo_fall_cancellation()
            elif choice == "3":
                self._print_header("Negative Fall Test (Normal Walk)")
                payload = {
                    "device_id": self.device_id,
                    "telemetry": {
                        "accel_x": 0.1,
                        "accel_y": 0.15,
                        "accel_z": 1.02,
                        "impact_magnitude_g": 1.05,
                        "tilt_angle_deg": 8.0,
                        "immobility_seconds": 0.0,
                    }
                }
                res = requests.post(f"{self.base_url}/api/emergency/fall/detect", json=payload).json()
                print(f"Assessment: {res.get('assessment', {}).get('reason')}")
            elif choice == "4":
                reason = input("Enter cancellation reason [False alarm]: ").strip() or "False alarm cancelled"
                res = requests.post(
                    f"{self.base_url}/api/emergency/sos/cancel",
                    json={"device_id": self.device_id, "reason": reason}
                )
                print(f"Status: {res.status_code} | {res.json()}")
            elif choice == "5":
                notes = input("Enter resolution notes [Assistance provided]: ").strip() or "Assistance provided"
                res = requests.post(
                    f"{self.base_url}/api/emergency/sos/resolve",
                    json={"device_id": self.device_id, "resolution_notes": notes}
                )
                print(f"Status: {res.status_code} | {res.json()}")
            elif choice == "6":
                st = requests.get(f"{self.base_url}/api/emergency/status/{self.device_id}").json()
                print(f"Live Status: {st}")
            elif choice == "7":
                self.demo_audit_trail()
            elif choice == "8":
                self.run_automated_demo()
            else:
                print("Invalid selection, please try again.")


def main():
    parser = argparse.ArgumentParser(description="Smart Blind Stick - Safety & Emergency Simulator")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="FastAPI backend base URL")
    parser.add_argument("--device-id", default="STICK_001", help="Device ID to simulate")
    parser.add_argument("--demo", action="store_true", help="Run automated end-to-end demo without prompt")
    args = parser.parse_args()

    sim = EmergencySimulator(base_url=args.base_url, device_id=args.device_id)
    if args.demo:
        sim.run_automated_demo()
    else:
        sim.run_interactive_menu()


if __name__ == "__main__":
    main()
