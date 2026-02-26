import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Floristik Kalkulator V24", layout="wide")

# --- BENUTZER-VERWALTUNG ---
LIZENZ_DATENBANK = {
    "Florist-1": {"name": "Florist-1-Laden", "valid_until": "2030-12-31"},
    "Florist-2": {"name": "Florist-2-Laden", "valid_until": "2030-12-31"},
    "Gast-Test-123": {"name": "Gastzugang", "valid_until": "2026-02-28"},
    "FDF-Duisburg": {"name": "Gastzugang-2", "valid_until": "2026-02-28"},
}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'active_field' not in st.session_state: st.session_state.active_field = "e0"
if 'num_buffer' not in st.session_state: st.session_state.num_buffer = ""

# --- LOGIN LOGIK ---
if not st.session_state.auth:
    st.title("🔐 Lizenz-Login")
    key_input = st.text_input("Lizenzschlüssel eingeben:", type="password")
    if st.button("Anmelden", use_container_width=True):
        if key_input in LIZENZ_DATENBANK:
            nutzer = LIZENZ_DATENBANK[key_input]
            if datetime.now() <= datetime.strptime(nutzer["valid_until"], "%Y-%m-%d"):
                st.session_state.auth = True
                st.session_state.user_name = nutzer["name"]
                st.rerun()
            else:
                st.error("Lizenz abgelaufen.")
        else:
            st.error("Falscher Schlüssel.")
    st.stop()

# --- CSS FÜR FARBEN & KOMPAKT-LAYOUT ---
st.markdown("""
<style>
    /* Hauptbuttons Design */
    div.stButton > button { 
        height: 3.2em !important; 
        font-weight: bold !important; 
        border-radius: 8px !important; 
        border: 1px solid #ccc !important;
    }
    
    /* Der rote Korrektur-Button (Minus) */
    .minus-btn button {
        background-color: #ff4b4b !important;
        color: white !important;
        height: 1.8em !important;
        width: 100% !important;
        font-size: 0.8em !important;
        padding: 0 !important;
        border: none !important;
    }

    /* Schnelles Numpad in der Sidebar */
    .numpad-grid button {
        height: 3.5em !important;
        background-color: #f0f2f6 !important;
        font-size: 1.2em !important;
    }
    
    /* Digitale Anzeige für Zusatzkosten */
    .val-box {
        background-color: #1e1e1e;
        color: #00ff00;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 1.8em;
        text-align: right;
        border: 2px solid #333;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISIERUNG DER DATEN ---
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
    val = float(st.session_state.num_buffer) / 100
    st.session_state[st.session_state.active_field] = val

# --- UI: SEITENLEISTE (ZUSATZKOSTEN) ---
with st.sidebar:
    st.subheader("Zusatzkosten (Touch)")
    
    # Feld-Auswahl
    c_f1, c_f2, c_f3 = st.columns(3)
    if c_f1.button("Gefäß", type="primary" if st.session_state.active_field=="e0" else "secondary"): 
        st.session_state.active_field="e0"; st.session_state.num_buffer=""
    if c_f2.button("Extra 1", type="primary" if st.session_state.active_field=="e1" else "secondary"): 
        st.session_state.active_field="e1"; st.session_state.num_buffer=""
    if c_f3.button("Extra 2", type="primary" if st.session_state.active_field=="e2" else "secondary"): 
        st.session_state.active_field="e2"; st.session_state.num_buffer=""
    
    # Digitale Anzeige
    current_val = st.session_state[st.session_state.active_field]
    st.markdown(f'<div class="val-box">{current_val:.2f} EUR</div>', unsafe_allow_html=True)

    # Numpad-Gitter
    st.markdown('<div class="numpad-grid">', unsafe_allow_html=True)
    for row in [[1,2,3], [4,5,6], [7,8,9]]:
        cols = st.columns(3)
        for i, num in enumerate(row):
            if cols[i].button(str(num), key=f"n_{num}", use_container_width=True):
                press_num(num)
                st.rerun()
    
    c_last = st.columns(3)
    if c_last[0].button("0", key="n_0", use_container_width=True):
        press_num(0)
        st.rerun()
    if c_last[1].button("C", key="n_clr", use_container_width=True):
        st.session_state[st.session_state.active_field] = 0.0
        st.session_state.num_buffer = ""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🚪 Abmelden"):
        st.session_state.auth = False
        st.rerun()

# --- BERECHNUNGEN ---
gruen_p = {"Pistazie": 1.50, "Euka": 2.50, "Salal": 1.50, "Baergras": 0.60, "Chico": 1.20}
schleif_p = {"Schleife kurz/schmal": 15.00, "Schleife lang/breit": 20.00}

mat_sum = sum(k * v for k, v in st.session_state.c_mat.items())
gruen_sum = sum(st.session_state.c_gruen[n] * gruen_p[n] for n in st.session_state.c_gruen)
schleif_sum = sum(st.session_state.c_schleife[n] * schleif_p[n] for n in st.session_state.c_schleife)
labor_sum = st.session_state.c_labor * 0.80
grand_total = mat_sum + gruen_sum + schleif_sum + labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2

# --- HEADER (METRIKEN) ---
m1, m2, m3 = st.columns(3)
m1.metric("Blumen & Grün", f"{mat_sum + gruen_sum:.2f} EUR")
m2.metric("Extras & Arbeit", f"{labor_sum + st.session_state.e0 + st.session_state.e1 + st.session_state.e2 + schleif_sum:.2f} EUR")
m3.subheader(f"GESAMT: {grand_total:.2f} EUR")

st.divider()

# --- HAUPTBEREICH (TABS) ---
t1, t2, t3, t4 = st.tabs(["🌸 Preise", "🌿 Grün", "🎀 Extras", "📋 Beleg"])

with t1:
    p_keys = sorted(st.session_state.c_mat.keys())
    for i in range(0, len(p_keys), 8):
        cols = st.columns(8)
        for j in range(8):
            if i + j < len(p_keys):
                p = p_keys[i+j]
                with cols[j]:
                    if st.button(f"{p:.2f}", key=f"m_{p}", use_container_width=True):
                        st.session_state.c_mat[p] += 1
                        st.rerun()
                    
                    # Inline-Minus: Anzahl und Button nebeneinander
                    count = st.session_state.c_mat[p]
                    if count > 0:
                        sub_l, sub_r = st.columns([1, 1])
                        sub_l.markdown(f"<div style='text-align:center; font-size:0.9em; padding-top:5px;'>{count}x</div>", unsafe_allow_html=True)
                        with sub_r:
                            st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
                            if st.button("—", key=f"min_m_{p}"):
                                st.session_state.c_mat[p] -= 1
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

with t2:
    g_cols = st.columns(5)
    for i, name in enumerate(gruen_p.keys()):
        with g_cols[i]:
            if st.button(f"{name}\n{gruen_p[name]:.2f}", key=f"g_{name}", use_container_width=True):
                st.session_state.c_gruen[name] += 1
                st.rerun()
            count = st.session_state.c_gruen[name]
            if count > 0:
                sub_l, sub_r = st.columns([1, 1])
                sub_l.markdown(f"<div style='text-align:center; padding-top:5px;'>{count}x</div>", unsafe_allow_html=True)
                with sub_r:
                    st.markdown('<div class="minus-btn">', unsafe_allow_html=True)
                    if st.button("—", key=f"min_g_{name}"):
                        st.session_state.c_gruen[name] -= 1
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

with t3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader("Arbeitszeit")
        if st.button("➕ 1 Min hinzufügen", key="btn_labor"): st.session_state.c_labor += 1; st.rerun()
        if st.session_state.c_labor > 0:
            st.info(f"Zeit: {st.session_state.c_labor} Min")
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
    st.button("♻️ ALLES LÖSCHEN", key="reset_btn", on_click=reset_callback, use_container_width=True)
    dt = []
    for p, c in st.session_state.c_mat.items():
        if c > 0: dt.append({"Pos": f"Material {p:.2f} EUR", "Anz": c, "Sum": p*c})
    for n, c in st.session_state.c_gruen.items():
        if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*gruen_p[n]})
    for n, c in st.session_state.c_schleife.items():
        if c > 0: dt.append({"Pos": n, "Anz": c, "Sum": c*schleif_p[n]})
    if st.session_state.c_labor > 0: dt.append({"Pos": "Arbeitszeit", "Anz": st.session_state.c_labor, "Sum": labor_sum})
    if st.session_state.e0 > 0: dt.append({"Pos": "Gefäß/Unterlage", "Anz": 1, "Sum": st.session_state.e0})
    if st.session_state.e1 > 0: dt.append({"Pos": "Extra 1", "Anz": 1, "Sum": st.session_state.e1})
    if st.session_state.e2 > 0: dt.append({"Pos": "Extra 2", "Anz": 1, "Sum": st.session_state.e2})
    
    if dt: 
        st.table(pd.DataFrame(dt))
        # PDF-Export
        def generate_pdf_file():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, "Kalkulations-Beleg", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(200, 10, f"Nutzer: {st.session_state.user_name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="C")
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(100, 8, "Position", border=1); pdf.cell(35, 8, "Anzahl", border=1); pdf.cell(45, 8, "Summe", border=1, ln=True)
            pdf.set_font("Arial", "", 12)
            for d in dt:
                pdf.cell(100, 8, str(d['Pos']), border=1); pdf.cell(35, 8, str(d['Anz']), border=1); pdf.cell(45, 8, f"{d['Sum']:.2f} EUR", border=1, ln=True)
            pdf.ln(10); pdf.set_font("Arial", "B", 14)
            pdf.cell(180, 10, f"GESAMT: {grand_total:.2f} EUR", ln=True, align="R")
            return pdf.output(dest="S").encode("latin-1")
        
        st.download_button("📄 BELEG ALS PDF SPEICHERN", data=generate_pdf_file(), file_name=f"Beleg_{datetime.now().strftime('%H%M')}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.write("Noch keine Positionen erfasst.")

st.markdown('</div>', unsafe_allow_html=True)
