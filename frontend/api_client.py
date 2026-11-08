"""Appels HTTP vers l'API FastAPI (avec cache court pour fluidifier l'interface)."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", API_URL).rstrip("/")  # adresse vue par le navigateur (iframe Dash)


def _get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def api_ok() -> bool:
    try:
        return requests.get(f"{API_URL}/api/health", timeout=3).ok
    except requests.RequestException:
        return False


@st.cache_data(ttl=60, show_spinner=False)
def get_filters():
    return _get("/api/filters")


@st.cache_data(ttl=60, show_spinner=False)
def get_offers(params: dict):
    return _get("/api/offers", params)


@st.cache_data(ttl=60, show_spinner=False)
def get_stats():
    return _get("/api/stats")


def generate_cv(payload: dict) -> dict:
    r = requests.post(f"{API_URL}/api/cv/generate", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def cv_pdf(cv: dict) -> bytes:
    r = requests.post(f"{API_URL}/api/cv/pdf", json=cv, timeout=60)
    r.raise_for_status()
    return r.content
