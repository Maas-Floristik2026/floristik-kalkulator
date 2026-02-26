import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V31", layout="wide")

# --- 2. BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "FDF-Duisburg": {"name": "FDF Gast", "valid_until": "2026-12-31"}
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "Gefäß"
if 'num_buffer' not in st.session_state: st.session_state.num_buffer = ""

# Login Logik
if not st.session_state.auth:
    st.title("🔐 Login")
    key = st.text_input("Lizenzschlüssel", type="password")
    if st.button("Anmelden"):
        if key in LIZENZ_DATENBANK:
            user_data = LIZENZ_DATENBANK[key]
            if datetime.now() <= datetime.strptime(user_data["valid_until"], "%Y-%m-%d"):
                st.session_state.auth = True
                st.session_state.user_name = user_data["name"]
                st.rerun()
            else:
                st.error("Lizenz abgelaufen.")
        else:
            st.error("Falscher Schlüssel.")
    st.stop()

# --- 3. CSS FÜR STABILITÄT (KEIN SPRINGEN) ---
st.markdown("""
<style>
    /* Jede Spalte im Gitter hat eine feste Höhe */
    [data-testid="column"] {
        min-height: 125px !important;
        max-height: 125px !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        margin-bottom: 5px !important;
    }

    /* Preis-Buttons Design */
    div.stButton > button {
        height: 3.2em !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
        background-color: white !important;
    }

    /* Die rote Badge (z.B. 1x) - Schwebend */
    .overlay-badge {
        position: absolute;
        top: -10px;
        right: 0px;
        background-color: #ff4b4b;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 0.75em;
        z-index: 10;
        border: 1px solid white;
    }

    /* Fester Platzhalter für den Minus-Button */
    .minus-container {
        height: 32px !important;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2px;
    }

    /* Roter Minus-Button */
    .minus-btn-style button {
        background-color: #fce4e4 !important;
        color: #e63946 !important;
        height: 1.8em !important;
        width: 100% !important;
        border: 1px solid #e63946 !important;
        font-size: 0.8em !important;
    }

    /* Numpad Digital-Anzeige */
    .val-box {
        background-color: #1e1e1e;
        color: #39FF14;
        padding: 10px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #444;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. DATEN INITIALISIERUNG ---
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

# --- 5. TURBO SIDEBAR (FRAGMENTS) ---
@st.fragment
def sidebar_numpad():
    st.subheader("Zusatzkosten (Touch)")
    
    option_map = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    selection = st.segmented_control(
        "Editieren:", 
        options=list(option_map.keys()), 
        default=st.session_state.active_field,
        key="cat_selection"
    )
    
    if selection != st.session_state.active_field:
        st.session_state.active_field = selection
        st.session_state.num_buffer = ""
        st.rerun()

    field_to_edit = option_map[st.session_state.active_field]
    st.markdown(f'<div class="val-box">{st.session_state[field_to_edit]:.2f} EUR</div>', unsafe_allow_html=True)

    # Numpad Buttons
    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, val in enumerate(row):
            if cols[i].button(str(val), key=f"n_{val}", use_container_width=True):
                st.session_state.num_buffer += str(val)
                st.session_state[field_to_edit] = float(st.session_state.num_buffer) / 100
                st.rerun()
    
    c_last = st.columns(3)
    if c_last[0].button("0", key="n_0", use_container_width=True):
        st.session_state.num_buffer += "0"
        st.session_state[field_to_edit] = float(st.session_state.num_buffer) / 100
        st.rerun()
    if c_last[1].button("C", key="n_clr", use_container_width=True):
        st.session_state[field_to_edit] = 0.0
        st.session_state.num_buffer = ""
        st.rerun()
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# --- 6. BERECHNUNG ---
gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Chico": 1.20}
schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}

s_blumen = sum(k * v for k, v in st.session_state.c_mat.items())
s_gruen = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
s_schleife = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
s_labor = st.session_state.c_labor * 0.80
gesamt = s_blumen + s_gruen + s_schleife + s_labor + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- 7. HAUPT-UI ---
with st.sidebar:
    sidebar_numpad()

# Metriken oben
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{s_blumen + s_gruen:.2f} EUR")
m2.metric("Extras & Arbeit", f"{s_labor + s_schleife + st.session_state.e0 + st.session_state.e1 + st.session_state.e2:.2f} EUR")
m3.subheader(f"GESAMT: {gesamt:.2f} EUR")

st.divider()
tabs = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Beleg"])

# Preise Tab
with tabs[0]:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p_val = p_keys[i+j]
                with cols[j]:
                    anzahl = st.session_state.c_mat[p_val]
                    # Rote Badge (Overlay)
                    if anzahl > 0:
                        st.markdown(f'<div class="overlay-badge">{anzahl}x</div>', unsafe_allow_html=True)
                    
                    if st.button(f"{p_val:.2f}", key=f"m_{p_val}", use_container_width=True):
                        st.session_state.c_mat[p_val] += 1
                        st.rerun()
                    
                    # Fester Minus-Platz
                    st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                    if anzahl > 0:
                        st.markdown('<div class="minus-btn-style">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_m_{p_val}", use_container_width=True):
                            st.session_state.c_mat[p_val] -= 1
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# Grün Tab
with tabs[1]:
    g_cols = st.columns(5)
    for i, g_name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            g_anz = st.session_state.c_gruen[g_name]
            if g_anz > 0:
                st.markdown(f'<div class="overlay-badge">{g_anz}x</div>', unsafe_allow_html=True)
            if st.button(f"{g_name}\n{gruen_p[g_name]:.2f}", key=f"g_{g_name}", use_container_width=True):
                st.session_state.c_gruen[g_name] += 1
                st.rerun()
            
            st.markdown('<div class="minus-container">', unsafe_allow_html=True)
            if g_anz > 0:
                st.markdown('<div class="minus-btn-style">', unsafe_allow_html=True)
                if st.button("—", key=f"min_g_{g_
