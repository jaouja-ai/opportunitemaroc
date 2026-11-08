
"""Lance l'API (+ dashboard Dash) et l'interface Streamlit d'un seul coup : python run.py"""
import subprocess
import sys
import time
import webbrowser

API_PORT, UI_PORT = "8000", "8501"


def main():
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", API_PORT])
    time.sleep(3)  # laisse l'API démarrer (et créer la base)
    ui = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", UI_PORT])
    time.sleep(4)
    webbrowser.open(f"http://localhost:{UI_PORT}")
    print(f"\nApplication : http://localhost:{UI_PORT}   |   API : http://localhost:{API_PORT}/docs   |   Ctrl+C pour arrêter\n")
    try:
        ui.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (ui, api):
            proc.terminate()


if __name__ == "__main__":
    main()
