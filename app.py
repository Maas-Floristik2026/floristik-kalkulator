import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V29", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
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

# --- CSS FÜR GESCHWINDIGKEIT & FIXIERTES GRID ---
st.markdown("""
<style>
    /* Verhindert das Springen der Seite bei Interaktion */
    [data-testid="stAppViewBlockContainer"] { padding-top: 2rem; }
    
    /* Zwingt das Gitter in eine absolut feste Struktur */
    div[data-testid="column"] {
        min-height: 110px !important;
        max-height: 110px !important;
    }

    /* Der Haupt-Button */
    div.stButton > button {
        width: 100% !important;
        height: 3.5em !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
    }

    /* Overlay Badge (Zähler) */
    .overlay-badge {
        position: absolute;
        top: -8px;
        right: 2px;
        background-color: #ff4b4b;
        color: white;
        padding: 1px 6px;
        border-radius: 10px;
        font-size: 0.75em;
        z-index: 10;
        border: 1px solid white;
        pointer-events: none; /* Klick geht durch das Badge auf den Button */
    }

    /* Kompakter Minus-Button unter dem Preis */
    .minus-container button {
        height: 1.6em !important;
        background-color: #f0f2f6 !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        margin-top: -5px !important;
        font-size: 0.8em !important;
    }

    /* Numpad Display */
    .val-box {
        background-color: #000;
        color: #39FF14;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #444;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# INITIALISIERUNG DER WERTE
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

# --- TURBO-SIDEBAR (Nur dieser Bereich lädt beim Tippen neu) ---
@st.fragment
def render_sidebar():
    st.subheader("Zusatzkosten (Touch)")
    
    # Schnellerer Wechsel durch Segmented Control
    option_map = {"Gefäß": "e0", "Extra 1": "e1", "Extra 2": "e2"}
    selection = st.segmented_control(
        "Kategorie wählen:", 
        options=list(option_map.keys()), 
        default=st.session_state.active_field
    )
    
    if selection != st.session_state.active_field:
        st.session_state.active_field = selection
        st.session_state.num_buffer = ""
        st.rerun()

    active_key = option_map[st.session_state.active_field]
    
    # Digitalanzeige
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
render_sidebar()

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
                    if count > 0:
                        st.markdown(f'<div class="overlay-badge">{count}x</div>', unsafe_allow_html=True)
                    if st.button(f"{p:.2f}", key=f"m_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1; st.rerun()
                    if count > 0:
                        st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_m_{p}", use_container_width=True):
                            st.session_state.c_mat[p] -= 1; st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    g_cols = st.columns(5)
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            count = st.session_state.c_gruen[name]
            if count > 0:
                st.markdown(f'<div class="overlay-badge">{count}x</div>', unsafe_allow_html=True)
            if st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1; st.rerun()
            if count > 0:
                st.markdown('<div class="minus-container">', unsafe_allow_html=True)
                if st.button("—", key=f"min_g_{name}", use_container_width=True):
                    st.session_state.c_gruen[name] -= 1; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button(f"➕ 1 Minute (0,80 EUR)", key="btn_labor", use_container_width=True): 
            st.session_state.c_labor += 1; st.rerun()
        if st.session_state.c_labor > 0:
            st.info(f"{st.session_state.c_labor} Min = {labor_sum:.2f} EUR")
            if st.button("— Minute abziehen", key="min_labor", use_container_width=True): 
                st.session_state.c_labor -= 1; st.rerun()
    with cb:
        st.subheader("Schleifen")
        for s_n, s_p in schleif_p.items():
            if st.button(f"{s_n} ({s_p} EUR)", key=f"s_{s_n}", use_container_width=True):
                st.session_state.c_schleife[s_n] += 1; st.rerun()
            if st.session_state.c_schleife[s_n] > 0:
                st.write(f"Anzahl: {st.session_state.c_schleife[s_n]}x")
                if st.button("— entfernen", key=f"min_s_{s_n}", use_container_width=True): 
                    st.session_state.c_schleife[s_n] -= 1; st.rerun()

with tabs[3]:
    st.button("♻️ ALLES LÖSCHEN (RESET)", key="reset", on_click=reset_callback, use_container_width=True)
    # (Beleg-Tabelle wie gehabt)

# --- GLOBALER RESET UNTEN ---
st.divider()
if st.button("♻️ KOMPLETT-RESET", key="global_reset", on_click=reset_callback): pass
