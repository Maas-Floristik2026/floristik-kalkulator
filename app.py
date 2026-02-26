import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- 1. SEITEN-EINSTELLUNGEN ---
st.set_page_config(page_title="Floristik Kalkulator V32", layout="wide")

# --- 2. LIZENZEN ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "Gast-Test-123": {"name": "Gastzugang", "valid_until": "2026-02-28"},
    "FDF-Duisburg": {"name": "FDF-Gast", "valid_until": "2026-12-31"}
}

# Session State Initialisierung
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "Gefäß"
if 'num_buffer' not in st.session_state: st.session_state.num_buffer = ""

# --- 3. LOGIN LOGIK ---
if not st.session_state.auth:
    st.title("🔐 Lizenz-Login")
    key_input = st.text_input("Lizenzschlüssel eingeben:", type="password")
    if st.button("Anmelden", use_container_width=True):
        if key_input in LIZENZ_DATENBANK:
            user_info = LIZENZ_DATENBANK[key_input]
            if datetime.now() <= datetime.strptime(user_info["valid_until"], "%Y-%m-%d"):
                st.session_state.auth = True
                st.session_state.user_name = user_info["name"]
                st.rerun()
            else:
                st.error("Lizenz abgelaufen.")
        else:
            st.error("Falscher Schlüssel.")
    st.stop()

# --- 4. DESIGN (CSS) ---
st.markdown("""
<style>
    /* Fixiert die Höhe der Gitter-Zellen */
    [data-testid="column"] {
        min-height: 130px !important;
        max-height: 130px !important;
        margin-bottom: 10px !important;
    }
    /* Preis Buttons */
    div.stButton > button {
        height: 3.2em !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    /* Zähler Badge */
    .overlay-badge {
        position: absolute;
        top: -10px;
        right: 0px;
        background-color: #ff4b4b;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 0.8em;
        z-index: 10;
        border: 1px solid white;
    }
    /* Platzhalter für Minus-Button */
    .minus-block {
        height: 35px !important;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 4px;
    }
    /* Roter Minus-Button */
    .minus-style button {
        background-color: #fee2e2 !important;
        color: #ef4444 !important;
        height: 1.8em !important;
        width: 100% !important;
        border: 1px solid #ef4444 !important;
        font-size: 0.8em !important;
    }
    /* Numpad Digital-Display */
    .digital-box {
        background-color: #1a1a1a;
        color: #00ff00;
        padding: 10px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #444;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. WERTE INITIALISIEREN ---
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gruen' not in st.session_state: st.session_state.c_gruen = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Chico": 0}
if 'c_schleife' not in st.session_state: st.session_state.c_schleife = {"Schleife kurz/schmal": 0, "Schleife lang/breit": 0}
if 'c_labor' not in st.session_state: st.session_state.c_labor = 0
if 'e0' not in st.session_state: st.session_state.e0 = 0.0
if 'e1' not in st.session_state: st.session_state.e1 = 0.0
if 'e2' not in st.session_state: st.session_state.e2 = 0.0

def reset_all():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gruen: st.session_state.c_gruen[k] = 0
    for k in st.session_state.c_schleife: st.session_state.c_schleife[k] = 0
    st.session_state.c_labor = 0
    st.session_state.e0 = 0.0
    st.session_state.e1 = 0.0
    st.session_state.e2 = 0.0
    st.session_state.num_buffer = ""

# --- 6. TURBO SIDEBAR FRAGMENT ---
@st.fragment
def render_numpad():
    st.subheader("Zusatzkosten (Touch)")
    
    # Kategorie-Wahl
    opts = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    choice = st.segmented_control("Editieren:", options=list(opts.keys()), default=st.session_state.active_field)
    
    if choice != st.session_state.active_field:
        st.session_state.active_field = choice
        st.session_state.num_buffer = ""
        st.rerun()

    field = opts[st.session_state.active_field]
    st.markdown(f'<div class="digital-box">{st.session_state[field]:.2f} EUR</div>', unsafe_allow_html=True)

    # Numpad Tasten
    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, val in enumerate(row):
            if cols[i].button(str(val), key=f"btn_{val}", use_container_width=True):
                st.session_state.num_buffer += str(val)
                st.session_state[field] = float(st.session_state.num_buffer) / 100
                st.rerun()
    
    last_row = st.columns(3)
    if last_row[0].button("0", key="btn_0", use_container_width=True):
        st.session_state.num_buffer += "0"
        st.session_state[field] = float(st.session_state.num_buffer) / 100
        st.rerun()
    if last_row[1].button("C", key="btn_clear", use_container_width=True):
        st.session_state[field] = 0.0
        st.session_state.num_buffer = ""
        st.rerun()
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# --- 7. BERECHNUN
