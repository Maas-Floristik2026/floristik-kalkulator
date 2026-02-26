import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V25", layout="wide")

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

# --- AGGRESSIVES CSS FÜR POSITIONIERUNG & PERFORMANCE ---
st.markdown("""
<style>
    /* Verhindert Scrollen beim Tippen */
    html { scroll-behavior: auto !important; }

    /* Preis Buttons */
    div.stButton > button { 
        height: 3em !important; 
        font-weight: bold !important; 
        border-radius: 8px !important; 
    }
    
    /* Zwingt Anzahl und Minus in EINE Zeile */
    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0px !important;
    }

    /* Roter Minus Button - Ultrakompakt */
    .minus-btn button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 1.5em !important;
        width: 100% !important;
        min-width: 20px !important;
        font-size: 0.8em !important;
        padding: 0 !important;
        border: none !important;
        line-height: 1 !important;
    }

    /* Numpad Design */
    .numpad-grid button {
        height: 3.5em !important;
        background-color: #f0f2f6 !important;
        font-size: 1.2em !important;
    }
    
    /* Grüne Digital-Anzeige */
    .val-box {
        background-color: #1e1e1e;
        color: #00ff00;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #333;
        margin-bottom: 5px;
    }

    /* Fixierter Footer für Reset & PDF */
    .footer-container {
        border-top: 2px solid #eee;
        padding-top: 20px;
        margin-top: 30px;
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

# --- SCHNELLE NUMPAD-LOGIK ---
def press_num(d):
    st.session_state.num_buffer += str(d)
    st.session_state[st.session_state.active_field] = float(st.session_state.num_buffer) / 100

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

# --- METRIKEN ---
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{mat_sum + gruen_sum:.2f} EUR")
m2.metric("Extras & Arbeit", f"{labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2 + schleif_sum:.2f} EUR")
m3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()

# --- TABS (NUR FÜR EINGABE) ---
t1, t2, t3, t4 = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Vorschau"])

with t1:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p = p_keys[i+j]
                with cols[j]:
                    if st.button(f"{p:.2f}", key=f"m_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1; st.rerun()
                    count = st.session_state.c_mat[p]
                    if count > 0:
                        sub_l, sub_r = st.columns([1, 1])
                        sub_l.markdown(f"<div style='text-align:right; font-size:0.85em; padding-top:2px;'>{count}x</div>", unsafe_allow_html=True)
                        with sub_r:
                            st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
                            if st.button("—", key=f"min_m_{p}"): st.session_state.c_mat[p] -= 1; st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    g_cols = st.columns(5)
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1; st.rerun()
            count = st.session_state.c_gruen[name]
            if count > 0:
                sub_l, sub_r = st.columns([1, 1])
                sub_l.markdown(f"<div style='text-align:right; font-size:0.85em; padding-top:2px;'>{count}x</div>", unsafe_allow_html=True)
                with sub_r:
                    st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
                    if st.button("—", key=f"min_g_{name}"): st.session_state.c_gruen[name] -= 1; st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

with t3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button("➕ 1 Min", key="btn_labor"): st.session_state.c_labor += 1; st.rerun()
        if st.session_state.c_labor > 0:
            st.write(f"Zeit: {st.session_state.c_labor} Min")
            if st.button("— Min abziehen", key="min_labor"): st.session_state.c_labor -= 1; st.rerun()
    with cb:
        st.subheader("Schleifen")
        for s_name, s_price in schleif_p.items():
            if st.button(f"{s_name} ({s_price} EUR)", key=f"s_{s_name}", use_container_width=True):
                st.session_state.c_schleife[s_name] += 1; st.rerun()
            if st.session_state.c_schleife[s_name] > 0:
                st.write(f"Anzahl: {st.session_state.c_schleife[s_name]}x")
                if st.button(f"— {s_name} entfernen", key=f"min_s_{s_name}"):
                    st.session_state.c_schleife[s_name] -= 1; st.rerun()

with t4:
    dt_preview = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt_preview.append({"Pos": f"Mat {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt_preview.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    if dt_preview: st.table(pd.DataFrame(dt_preview))
    else: st.write("Keine Positionen.")

# --- GLOBALER FOOTER (FÜR ALLE REITER SICHTBAR) ---
st.markdown('<div class="footer-container">', unsafe_allow_html=True)
f1, f2 = st.columns(2)
with f1:
    st.button("♻️ ALLES LÖSCHEN (RESET)", key="global_reset", on_click=reset_callback, use_container_width=True)

with f2:
    # PDF Logik
    dt_final = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt_final.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt_final.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    for n, c in st.session_state.c_schleife.items():
        if c > 0: dt_final.append({"Pos": n, "Anz": c, "Sum": c*schleif_p[n]})
    if st.session_state.c_labor > 0: dt_final.append({"Pos": "Arbeitszeit", "Anz": st.session_state.c_labor, "Sum": labor_sum})
    if st.session_state.e0 > 0: dt_final.append({"Pos": "Gefäß", "Sum": st.session_state.e0, "Anz": 1})
    if st.session_state.e1 > 0: dt_final.append({"Pos": "Extra 1", "Sum": st.session_state.e1, "Anz": 1})
    if dt_final:
        def get_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulations-Beleg", ln=True, align="C")
            pdf.set_font("Arial", "", 12)
            for d in dt_final:
                pdf.cell(100, 8, str(d['Pos']), 1)
                pdf.cell(40, 8, str(d['Anz']), 1)
                pdf.cell(40, 8, f"{d['Sum']:.2f} EUR", 1, ln=True)
            pdf.ln(10)
            pdf.cell(180, 10, f"GESAMT: {grand_total:.2f} EUR", 0, 1, 'R')
            return pdf.output(dest="S").encode("latin-1")
        st.download_button("📄 PDF SPEICHERN", data=get_pdf(), file_name="Beleg.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.button("📄 PDF (Liste leer)", disabled=True, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
