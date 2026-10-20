"""
Master Launcher for Smart Blind Stick System.

Allows starting the backend, opening the live Guardian Web Dashboard,
connecting physical USB/WiFi hardware, launching AI Vision, or running
hardware simulations from a single convenient menu.

Usage:
    python run_all.py
"""
import os
import sys
import time
import subprocess
import webbrowser

PYTHON_EXE = sys.executable

BANNER = """
================================================================================
🦯  SMART BLIND STICK - MASTER SYSTEM LAUNCHER
   AI Vision, Multi-Sensor IoT, Real-Time GPS & Emergency Guardian System
================================================================================
"""

MENU = """
Please select an operation:

  [1]  Start Backend Server & Launch Guardian Web Dashboard
  [2]  Connect Physical Hardware via USB Serial Bridge (ESP32 / Arduino)
  [3]  Connect Camera & Run AI Vision Obstacle Detection (Webcam / USB)
  [4]  Run Device & Sensor Simulator (Test without physical hardware)
  [5]  Run Safety & Emergency Subsystem Interactive Simulator
  [6]  Run Complete Automated Pytest Suite
  [0]  Exit
================================================================================
"""


def check_server_running(url="http://127.0.0.1:8000/health"):
    try:
        import requests
        r = requests.get(url, timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def start_backend_and_dashboard():
    print("\n[*] Starting FastAPI Backend Server...")
    proc = subprocess.Popen([PYTHON_EXE, "run.py"])
    print("[*] Waiting for server to initialize...")
    for _ in range(15):
        time.sleep(0.5)
        if check_server_running():
            break

    dashboard_url = "http://127.0.0.1:8000/dashboard"
    app_url = "http://127.0.0.1:8000/app"
    print(f"\n[+] Backend is LIVE at:               http://127.0.0.1:8000")
    print(f"[+] Live Stick Mobile Companion (PWA): {app_url}")
    print(f"[+] Guardian Live Monitor Dashboard:   {dashboard_url}")
    print(f"[+] API Swagger Docs:                  http://127.0.0.1:8000/docs")
    print("\n[*] Opening Guardian Web Dashboard in your default browser...")
    try:
        webbrowser.open(app_url)
    except Exception:
        pass

    print("\n[!] Backend server is running. Press Ctrl+C in this terminal to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down backend server...")
        proc.terminate()


def start_serial_bridge():
    print("\n[*] Launching Bidirectional Serial Hardware Bridge...")
    subprocess.run([PYTHON_EXE, "scripts/serial_hardware_bridge.py"])


def start_ai_vision():
    print("\n[*] Launching AI Vision Camera Detection Pipeline...")
    subprocess.run([PYTHON_EXE, "scripts/run_vision_hardware.py"])


def run_device_simulator():
    print("\n[*] Running Smart Stick Hardware Simulator...")
    subprocess.run([PYTHON_EXE, "scripts/simulate_device.py"])


def run_emergency_simulator():
    print("\n[*] Running Safety & Emergency Interactive Simulator...")
    subprocess.run([PYTHON_EXE, "scripts/simulate_emergency.py"])


def run_tests():
    print("\n[*] Executing Automated Test Suite (Pytest)...")
    subprocess.run([PYTHON_EXE, "-m", "pytest", "-v"])


def main():
    while True:
        print(BANNER)
        print(MENU)
        try:
            choice = input("Enter choice (0-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if choice == "1":
            start_backend_and_dashboard()
        elif choice == "2":
            start_serial_bridge()
        elif choice == "3":
            start_ai_vision()
        elif choice == "4":
            run_device_simulator()
        elif choice == "5":
            run_emergency_simulator()
        elif choice == "6":
            run_tests()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("[!] Invalid option. Please enter 0-6.")
        
        input("\nPress Enter to return to main menu...")


if __name__ == "__main__":
    main()
