import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V30", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "Gast-Test": {"name": "Gast", "valid_until": "2026-12-31"}
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "Gefäß"
if 'num_buffer' not in st.session_state: st.session_state.num_buffer = ""

# LOGIN
if not st.session_state.auth:
    st.title("🔐 Login")
    key = st.text_input("Lizenzschlüssel", type="password")
    if st.button("Anmelden"):
        if key in LIZENZ_DATENBANK:
            st.session_state.auth = True
            st.session_state.user_name = LIZENZ_DATENBANK[key]["name"]
            st.rerun()
    st.stop()

# --- CSS FÜR EIN UNZERSTÖRBARES GRID & PERFORMANCE ---
st.markdown("""
<style>
    /* Zwingt jede Preis-Spalte auf eine absolut identische Höhe */
    [data-testid="column"] {
        min-height: 125px !important;
        max-height: 125px !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow: visible !important;
    }

    /* Haupt-Preis Buttons */
    div.stButton > button {
        height: 3.2em !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
        background-color: white !important;
    }

    /* Die Badge (z.B. 1x) - Jetzt schwebend rechts oben am Button */
    .overlay-badge {
        position: absolute;
        top: -8px;
        right: -2px;
        background-color: #ff4b4b;
        color: white;
        padding: 1px 6px;
        border-radius: 10px;
        font-size: 0.75em;
        z-index: 10;
        border: 1px solid white;
    }

    /* Minus-Container mit fester Höhe verhindert das Springen des Gitters */
    .minus-space {
        height: 35px !important;
        margin-top: 4px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .minus-btn button {
        background-color: #f0f2f6 !important;
        color: #ff4b4b !important;
        height: 1.8em !important;
        width: 100% !important;
        border: 1px solid #ff4b4b !important;
        font-size: 0.8em !important;
        line-height: 1 !important;
    }

    /* Numpad Design */
    .val-box {
        background-color: #000;
        color: #39FF14;
        padding: 12px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #444;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# INITIALISIERUNG
if 'c_mat' not in st.session_state: st.session_state.c_mat = {round(x * 0.1, 2): 0 for x in range(5, 101)}
if 'c_gruen' not in st.session_state: st.session_state.c_gruen = {"Pistazie": 0, "Euka": 0, "Salal": 0, "Baergras": 0, "Chico": 0}
if 'c_schleife' not in st.session_state: st.session_state.c_schleife = {"Schleife kurz/schmal": 0, "Schleife lang/breit": 0}
if 'c_labor' not in st.session_state: st.session_state.c_labor = 0
if 'e0' not in st.session_state: st.session_state.e0 = 0.0
if 'e1' not in st.session_state: st.session_state.e1 = 0.0
if 'e2' not in st.session_state: st.session_state.e2 = 0.0

def reset_callback():
    for k in st.session_state.c_mat: st.session_state.c_mat[k] = 0
    for k in st.session_state.c_gruen: st.session_state.c_gruen[k] = 0
    for k in st.session_state.c_schleife: st.session_state.c_schleife[k] = 0
    st.session_state.c_labor = 0
    st.session_state.e0, st.session_state.e1, st.session_state.e2 = 0.0, 0.0, 0.0
    st.session_state.num_buffer = ""

# --- TURBO-SIDEBAR (Isoliertes Fragment für Speed) ---
@st.fragment
def sidebar_numpad():
    st.subheader("Zusatzkosten (Touch)")
    
    option_map = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    selection = st.segmented_control(
        "Kategorie wählen:", 
        options=list(option_map.keys()), 
        default=st.session_state.active_field,
        key="cat_select"
    )
    
    if selection != st.session_state.active_field:
        st.session_state.active_field = selection
        st.session_state.num_buffer = ""
        st.rerun()

    active_key = option_map[st.session_state.active_field]
    st.markdown(f'<div class="val-box">{st.session_state[active_key]:.2f} EUR</div>', unsafe_allow_html=True)

    # Numpad
    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, num in enumerate(row):
            if cols[i].button(str(num), key=f"n_{num}", use_container_width=True):
                st.session_state.num_buffer += str(num)
                st.session_state[active_key] = float(st.session_state.num_buffer) / 100
                st.rerun()
    
    c_l = st.columns(3)
    if c_l[0].button("0", key="n_0", use_container_width=True):
        st.session_state.num_buffer += "0"
        st.session_state[active_key] = float(st.session_state.num_buffer) / 100
        st.rerun()
    if c_l[1].button("C", key="n_clr", use_container_width=True):
        st.session_state[active_key] = 0.0
        st.session_state.num_buffer = ""
        st.rerun()
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# --- HAUPTBEREICH ---
with st.sidebar:
    sidebar_numpad()

# BERECHNUNG
gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Chico": 1.20}
schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}
mat_sum = sum(k * v for k, v in st.session_state.c_mat.items())
gruen_sum = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
schleif_sum = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
labor_sum = st.session_state.c_labor * 0.80
grand_total = mat_sum + gruen_sum + schleif_sum + labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# HEADER
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{mat_sum + gruen_sum:.2f} EUR")
m2.metric("Extras & Arbeit", f"{labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2 + schleif_sum:.2f} EUR")
m3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()
tabs = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Beleg"])

with tabs[0]:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p = p_keys[i+j]
                with cols[j]:
                    count = st.session_state.c_mat[p]
                    # Rote Badge (Overlay)
                    if count > 0:
                        st.markdown(f
