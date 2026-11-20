"""Appels HTTP vers l'API FastAPI (avec cache court pour fluidifier l'interface)."""
import os
import time

import requests
import streamlit as st


def _setting(name, default):
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, default)


API_URL = _setting("API_URL", "http://localhost:8000").rstrip("/")
PUBLIC_API_URL = _setting("PUBLIC_API_URL", API_URL).rstrip("/")


def _get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def api_ok() -> bool:
    for _ in range(12):
        try:
            if requests.get(f"{API_URL}/api/filters", timeout=8).ok:
                return True
        except requests.RequestException:
            pass
        time.sleep(5)
    return False
def api_diag() -> str:
    """Affiche l'URL utilisée et l'erreur réelle (temporaire)."""
    try:
        r = requests.get(f"{API_URL}/api/filters", timeout=60)
        return f"URL = {API_URL} | statut = {r.status_code}"
    except Exception as e:
        return f"URL = {API_URL} | ERREUR = {type(e).__name__}: {e}"