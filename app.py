import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V27", layout="wide")

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

# --- CSS FÜR EIN UNZERSTÖRBARES GRID ---
st.markdown("""
<style>
    /* Fixiert die Höhe jeder Zelle im Gitter, damit NICHTS mehr springt */
    [data-testid="column"] {
        height: 100px !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        margin-bottom: 10px !important;
    }

    /* Preis Buttons */
    div.stButton > button { 
        height: 3.5em !important; 
        font-weight: bold !important; 
        border-radius: 8px !important;
        z-index: 1;
    }
    
    /* Der rote Minus Button - Ultrakompakt und schwebend */
    .minus-area {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: rgba(240, 242, 246, 0.9);
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 0px 4px;
        height: 22px;
        margin-top: -15px; /* Zieht das Element nach oben ÜBER den Button-Rand */
        z-index: 10;
        position: relative;
    }

    .minus-btn-style button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 18px !important;
        width: 18px !important;
        min-width: 18px !important;
        font-size: 14px !important;
        line-height: 1 !important;
        padding: 0 !important;
        border: none !important;
    }

    /* Numpad Design Optimierung für Speed */
    .numpad-container button {
        height: 3.5em !important;
        font-size: 1.3em !important;
        background-color: #f8f9fb !important;
    }
    
    /* Grüne Digital-Anzeige */
    .val-box {
        background-color: #000;
        color: #39FF14;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #333;
        margin-bottom: 15px;
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

# --- SCHNELLE NUMPAD LOGIK ---
def press_num(d):
    st.session_state.num_buffer = st.session_state.num_buffer + str(d)
    try:
        st.session_state[st.session_state.active_field] = float(st.session_state.num_buffer) / 100
    except:
        pass

# --- UI: SIDEBAR ---
with st.sidebar:
    st.subheader("Zusatzkosten (Touch)")
    
    c_f1, c_f2, c_f3 = st.columns(3)
    if c_f1.button("Gefäß", type="primary" if st.session_state.active_field=="e0" else "secondary"): 
        st.session_state.active_field="e0"; st.session_state.num_buffer=""
    if c_f2.button("Extra 1", type="primary" if st.session_state.active_field=="e1" else "secondary"): 
        st.session_state.active_field="e1"; st.session_state.num_buffer=""
    if c_f3.button("Extra 2", type="primary" if st.session_state.active_field=="e2" else "secondary"): 
        st.session_state.active_field="e2"; st.session_state.num_buffer=""
    
    st.markdown(f'<div class="val-box">{st.session_state[st.session_state.active_field]:.2f} EUR</div>', unsafe_allow_html=True)

    # Numpad - flüssiger durch direkten Zugriff
    st.markdown('<div class="numpad-container">', unsafe_allow_html=True)
    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, num in enumerate(row):
            if cols[i].button(str(num), key=f"n_{num}", use_container_width=True):
                press_num(num); st.rerun()
    
    c_last = st.columns(3)
    if c_last[0].button("0", key="n_0", use_container_width=True): press_num(0); st.rerun()
    if c_last[1].button("C", key="n_clr", use_container_width=True):
        st.session_state[st.session_state.active_field] = 0.0
        st.session_state.num_buffer = ""; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False; st.rerun()

# --- BERECHNUNG ---
gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Chico": 1.20}
schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}
mat_sum = sum(k * v for k, v in st.session_state.c_mat.items())
gruen_sum = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
schleif_sum = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
labor_sum = st.session_state.c_labor * 0.80
grand_total = mat_sum + gruen_sum + schleif_sum + labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- HEADER ---
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{mat_sum + gruen_sum:.2f} EUR")
m2.metric("Extras & Arbeit", f"{labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2 + schleif_sum:.2f} EUR")
m3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Vorschau"])

with t1:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p = p_keys[i+j]
                with cols[j]:
                    # Hauptbutton
                    if st.button(f"{p:.2f}", key=f"m_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1; st.rerun()
                    
                    # Korrekturbereich - wird ÜBER dem nächsten Button eingeblendet
                    count = st.session_state.c_mat[p]
                    if count > 0:
                        st.markdown(f'<div class="minus-area"><span>{count}x</span>', unsafe_allow_html=True)
                        st.markdown('<div class="minus-btn-style">', unsafe_allow_html=True)
                        if st.button("—", key=f"min_m_{p}"): st.session_state.c_mat[p] -= 1; st.rerun()
                        st.markdown('</div></div>', unsafe_allow_html=True)

with t2:
    g_cols = st.columns(5)
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1; st.rerun()
            count = st.session_state.c_gruen[name]
            if count > 0:
                st.markdown(f'<div class="minus-area"><span>{count}x</span>', unsafe_allow_html=True)
                st.markdown('<div class="minus-btn-style">', unsafe_allow_html=True)
                if st.button("—", key=f"min_g_{name}"): st.session_state.c_gruen[name] -= 1; st.rerun()
                st.markdown('</div></div>', unsafe_allow_html=True)

with t3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        # Wunsch: Anzeige der 0.80 EUR
        if st.button("➕ 1 Minute (0,80 EUR)", key="btn_labor", use_container_width=True): 
            st.session_state.c_labor += 1; st.rerun()
        if st.session_state.c_labor > 0:
            st.info(f"Zeit: {st.session_state.c_labor} Min = {labor_sum:.2f} EUR")
            if st.button("— Minute abziehen", key="min_labor", use_container_width=True): 
                st.session_state.c_labor -= 1; st.rerun()
    with cb:
        st.subheader("Schleifen")
        for s_name, s_price in schleif_p.items():
            if st.button(f"{s_name} ({s_price} EUR)", key=f"s_{s_name}", use_container_width=True):
                st.session_state.c_schleife[s_name] += 1; st.rerun()
            if st.session_state.c_schleife[s_name] > 0:
                st.write(f"Anzahl: {st.session_state.c_schleife[s_name]}x")
                if st.button(f"— {s_name} entfernen", key=f"min_s_{s_name}", use_container_width=True):
                    st.session_state.c_schleife[s_name] -= 1; st.rerun()

with t4:
    dt_p = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt_p.append({"Pos": f"Mat {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt_p.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    if dt_p: st.table(pd.DataFrame(dt_p))
    else: st.write("Keine Positionen erfasst.")

# --- GLOBALER FOOTER ---
st.divider()
f1, f2 = st.columns(2)
with f1:
    st.button("♻️ ALLES LÖSCHEN (RESET)", key="global_reset", on_click=reset_callback, use_container_width=True)

with f2:
    dt_f = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt_f.append({"Pos": f"Mat {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt_f.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    for n, c in st.session_state.c_schleife.items():
        if c > 0: dt_f.append({"Pos": n, "Anz": c, "Sum": c*schleif_p[n]})
    if st.session_state.c_labor > 0: dt_f.append({"Pos": "Arbeit", "Anz": st.session_state.c_labor, "Sum": labor_sum})
    if st.session_state.e0 > 0: dt_f.append({"Pos": "Gefäß", "Anz": 1, "Sum": st.session_state.e0})
    if st.session_state.e1 > 0: dt_f.append({"Pos": "Extra 1", "Anz": 1, "Sum": st.session_state.e1})
    if st.session_state.e2 > 0: dt_f.append({"Pos": "Extra 2", "Anz": 1, "Sum": st.session_state.e2})
    
    if dt_f:
        def get_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulations-Beleg", ln=True
