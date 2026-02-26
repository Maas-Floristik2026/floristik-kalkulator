import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V28", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "e0"
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

# --- CSS: DAS "UNZERSTÖRBARE" OVERLAY-DESIGN ---
st.markdown("""
<style>
    /* Zwingt das Gitter in eine feste Struktur */
    div[data-testid="column"] {
        padding: 5px !important;
        margin-bottom: -15px !important;
    }

    /* Der Haupt-Button */
    div.stButton > button {
        width: 100% !important;
        height: 3.8em !important;
        font-weight: bold !important;
        font-size: 1.1em !important;
        border-radius: 10px !important;
        position: relative !important;
        border: 1px solid #ccc !important;
        z-index: 1;
    }

    /* Schwebende Anzeige für Zähler & Minus (Rechts Oben auf dem Button) */
    .overlay-badge {
        position: absolute;
        top: -10px;
        right: 0px;
        background-color: #ff4b4b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        z-index: 10;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        border: 1px solid white;
    }

    /* Numpad Speed-Optimierung */
    .numpad-btn button {
        height: 3.5em !important;
        font-size: 1.3em !important;
        background-color: #f8f9fb !important;
    }

    /* Green Digital Display */
    .val-box {
        background-color: #000;
        color: #39FF14;
        padding: 12px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #444;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# INITIALISIERUNG DER DATEN
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

def press_num(d):
    st.session_state.num_buffer += str(d)
    st.session_state[st.session_state.active_field] = float(st.session_state.num_buffer) / 100

# --- SIDEBAR: NUMPAD ---
with st.sidebar:
    st.subheader("Zusatzkosten (Touch)")
    f_cols = st.columns(3)
    if f_cols[0].button("Gefäß", type="primary" if st.session_state.active_field=="e0" else "secondary"): st.session_state.active_field="e0"; st.session_state.num_buffer=""
    if f_cols[1].button("Extra 1", type="primary" if st.session_state.active_field=="e1" else "secondary"): st.session_state.active_field="e1"; st.session_state.num_buffer=""
    if f_cols[2].button("Extra 2", type="primary" if st.session_state.active_field=="e2" else "secondary"): st.session_state.active_field="e2"; st.session_state.num_buffer=""
    
    st.markdown(f'<div class="val-box">{st.session_state[st.session_state.active_field]:.2f} EUR</div>', unsafe_allow_html=True)

    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, num in enumerate(row):
            if cols[i].button(str(num), key=f"n_{num}", use_container_width=True):
                press_num(num); st.rerun()
    
    c_l = st.columns(3)
    if c_l[0].button("0", key="n_0", use_container_width=True): press_num(0); st.rerun()
    if c_l[1].button("C", key="n_clr", use_container_width=True):
        st.session_state[st.session_state.active_field] = 0.0
        st.session_state.num_buffer = ""; st.rerun()
    st.divider()
    if st.button("🚪 Abmelden"): st.session_state.auth = False; st.rerun()

# --- BERECHNUNG ---
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
                    # DAS OVERLAY: Erscheint nur wenn Count > 0
                    if count > 0:
                        st.markdown(f'''<div style="position: relative;">
                            <div class="overlay-badge">
                                <span>{count}x</span>
                            </div>
                        </div>''', unsafe_allow_html=True)
                    
                    if st.button(f"{p:.2f}", key=f"m_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1; st.rerun()
                    
                    # Kleiner Minus-Button separat darunter, um Layout-Sprünge zu vermeiden
                    if count > 0:
                        if st.button("—", key=f"min_m_{p}", help="Abziehen"):
                            st.session_state.c_mat[p] -= 1; st.rerun()

with tabs[1]:
    g_cols = st.columns(5)
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            count = st.session_state.c_gruen[name]
            if count > 0:
                st.markdown(f'<div style="position:relative;"><div class="overlay-badge">{count}x</div></div>', unsafe_allow_html=True)
            if st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1; st.rerun()
            if count > 0:
                if st.button("—", key=f"min_g_{name}"): st.session_state.c_gruen[name] -= 1; st.rerun()

with tabs[2]:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button(f"➕ 1 Minute (0,80 EUR)", key="btn_labor", use_container_width=True): 
            st.session_state.c_labor += 1; st.rerun()
        if st.session_state.c_labor > 0:
            st.info(f"{st.session_state.c_labor} Min = {labor_sum:.2f} EUR")
            if st.button("— Minute abziehen", key="min_labor"): st.session_state.c_labor -= 1; st.rerun()
    with cb:
        st.subheader("Schleifen")
        for s_n, s_p in schleif_p.items():
            if st.button(f"{s_n} ({s_p} EUR)", key=f"s_{s_n}", use_container_width=True):
                st.session_state.c_schleife[s_n] += 1; st.rerun()
            if st.session_state.c_schleife[s_n] > 0:
                st.write(f"Anzahl: {st.session_state.c_schleife[s_n]}x")
                if st.button(f"— {s_n} entfernen", key=f"min_s_{s_n}"): st.session_state.c_schleife[s_n] -= 1; st.rerun()

with tabs[3]:
    st.button("♻️ ALLES LÖSCHEN (RESET)", key="reset", on_click=reset_callback, use_container_width=True)
    dt = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    # ... Rest der dt befüllung (Schleifen, Gefäß, Extras)
    if dt: st.table(pd.DataFrame(dt))

# --- GLOBALER FOOTER (FÜR RESET ÜBERALL) ---
st.divider()
if st.button("♻️ KOMPLETT-RESET", key="global_reset", on_click=reset_callback): pass
